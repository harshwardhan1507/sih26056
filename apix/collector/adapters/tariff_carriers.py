"""
Additional Carrier Tariff-Sheet Adapters — Tier 2 Fare Sources for APIx.

Implements tariff-sheet adapters for:
  - Air India (AI): mandated under Rule 135(2)
  - Akasa Air (QP): mandated under Rule 135(2)

Both derive from the same base as the IndiGo adapter and share ONE definition
of "the declared fare for this route and advance window"
(``tariff_sheet.band_fare_for_window``). They previously used a different rule
from the IndiGo adapter -- Maximum-row overall midpoint versus Minimum-row
floor -- which put carriers on incompatible price definitions inside the same
matched sample.

What a tariff sheet is, and is not
----------------------------------
These are DGCA-mandated *declared fare bands*: a regulatory floor and ceiling
per inventory bucket, republished monthly. They are NOT transacted consumer
prices, and they do NOT move day to day within a month. Treat this tier as a
level reference and a coverage backstop, not as a daily price signal --
see ``docs/METHODOLOGY_CHAIN_DRIFT.md`` §"Tariff sheets in the matched sample".
"""

from __future__ import annotations

import csv
from datetime import date, datetime, timedelta, timezone
import logging
from pathlib import Path
from typing import Optional

from .base import FareQuote, FareSource
from .tariff_sheet import (
    TariffBand,
    band_fare_for_window,
    parse_indigo_tariff_pdf,
)

logger = logging.getLogger(__name__)

_FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
AI_FIXTURE_CSV = _FIXTURE_DIR / "air_india_tariff_basket_rows.csv"
QP_FIXTURE_CSV = _FIXTURE_DIR / "akasa_tariff_basket_rows.csv"

_N_FARE_BUCKETS = 21


def parse_carrier_tariff_csv(
    path: Path | str,
    carrier_iata: str,
    source_url: str = "",
    effective_month: Optional[str] = None,
) -> list[TariffBand]:
    """
    Parse a pre-committed carrier tariff basket CSV into TariffBand instances.

    ``effective_month`` is derived from the filename when not supplied. It used
    to be hardcoded to "2026-09", so every parsed band claimed to be current
    regardless of which sheet it actually came from.
    """
    csv_path = Path(path)
    if not csv_path.exists():
        raise FileNotFoundError(f"Fixture CSV not found: {csv_path}")

    resolved_month = effective_month or _month_from_name(csv_path.name)
    retrieved_at = datetime.now(timezone.utc)

    bands: list[TariffBand] = []
    with open(csv_path, mode="r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for line_no, row in enumerate(reader, start=2):
            orig = row["origin_iata"].strip().upper()
            dest = row["destination_iata"].strip().upper()
            row_type = row["row_type"].strip()

            try:
                dist_km = int(row["distance_km"]) if row.get("distance_km") else None
            except ValueError:
                logger.warning(
                    "%s line %d: unparseable distance_km %r; recording as unknown.",
                    csv_path.name, line_no, row.get("distance_km"),
                )
                dist_km = None

            buckets: list[Optional[float]] = []
            for i in range(1, _N_FARE_BUCKETS + 1):
                val_str = (row.get(f"fare_{i}") or "").strip()
                if not val_str or val_str in ("None", "null", "NA"):
                    buckets.append(None)
                    continue
                try:
                    buckets.append(float(val_str))
                except ValueError:
                    # Surface malformed money rather than swallowing it: a
                    # silent None here is indistinguishable from a genuine
                    # "NA" bucket in the published sheet.
                    logger.warning(
                        "%s line %d: unparseable fare_%d %r; treating as blank.",
                        csv_path.name, line_no, i, val_str,
                    )
                    buckets.append(None)

            non_none = [b for b in buckets if b is not None]

            bands.append(TariffBand(
                origin_iata=orig,
                destination_iata=dest,
                row_type=row_type,
                distance_km=dist_km,
                fares=buckets,
                min_fare_inr=min(non_none) if non_none else None,
                max_fare_inr=max(non_none) if non_none else None,
                source_url=source_url or str(csv_path),
                retrieved_at_utc=retrieved_at,
                effective_month=resolved_month,
                notes=(
                    f"Carrier {carrier_iata} DGCA Rule 135(2) declared tariff band. "
                    "Regulatory floor/ceiling, not a transacted fare. "
                    "Base fare only; mandatory taxes and fees excluded."
                ),
            ))

    return bands


def _month_from_name(name: str) -> Optional[str]:
    """Extract YYYY-MM from a filename, if it carries one."""
    import re
    m = re.search(r"(\d{4})[-_](\d{2})", name)
    return f"{m.group(1)}-{m.group(2)}" if m else None


class BaseCarrierTariffSheetSource(FareSource):
    """
    Shared Tier 2 adapter for a single carrier's DGCA-mandated tariff sheet.

    Set ``use_fixture=False`` together with ``pdf_path`` to parse a live sheet.
    ``use_fixture=False`` on its own used to be silently ignored -- the adapter
    read the fixture regardless -- so a caller could believe it was on live
    data when it was not. It now raises.
    """

    def __init__(
        self,
        carrier_iata: str,
        source_id: str,
        fixture_csv: Path,
        use_fixture: bool = True,
        pdf_path: Optional[Path] = None,
    ) -> None:
        if not use_fixture and pdf_path is None:
            raise ValueError(
                f"{source_id}: use_fixture=False requires an explicit pdf_path. "
                "No live tariff-sheet URL is configured for this carrier, so "
                "there is nothing to fetch. Either pass pdf_path=<downloaded "
                "sheet> or keep use_fixture=True."
            )

        self.carrier_iata = carrier_iata.strip().upper()
        self.source_id = source_id
        self.collection_method = "tariff_sheet"
        self._fixture_csv = Path(fixture_csv)
        self._use_fixture = use_fixture
        self._pdf_path = Path(pdf_path) if pdf_path else None
        self._bands_cache: Optional[list[TariffBand]] = None

    def _get_bands(self) -> list[TariffBand]:
        if self._bands_cache is None:
            if self._use_fixture:
                self._bands_cache = parse_carrier_tariff_csv(
                    self._fixture_csv, carrier_iata=self.carrier_iata
                )
            else:
                assert self._pdf_path is not None  # guaranteed by __init__
                self._bands_cache = parse_indigo_tariff_pdf(
                    self._pdf_path, source_url=str(self._pdf_path)
                )
        return self._bands_cache

    def get_quotes(
        self,
        origin: str,
        destination: str,
        as_of_date: date,
        advance_window_days: int,
        carriers: list[str],
    ) -> list[FareQuote]:
        normalized = [c.strip().upper() for c in carriers]
        if self.carrier_iata not in normalized:
            return []

        try:
            bands = self._get_bands()
        except Exception as exc:
            logger.warning("%s: failed to load tariff bands: %s", self.source_id, exc)
            return []

        fare = band_fare_for_window(bands, origin, destination, advance_window_days)
        if fare is None:
            return []

        return [
            FareQuote(
                collected_at_utc=datetime.now(timezone.utc),
                # The flight quoted today departs advance_window_days later.
                departure_date=as_of_date + timedelta(days=advance_window_days),
                advance_window_days=advance_window_days,
                origin_iata=origin.strip().upper(),
                destination_iata=destination.strip().upper(),
                carrier_iata=self.carrier_iata,
                fare_class="Economy",
                total_fare_inr=round(fare, 2),
                source_id=self.source_id,
                collection_method=self.collection_method,
                quality_flag="ok",
            )
        ]


# Retained for backwards compatibility with the original private name.
_BaseCarrierTariffSheetSource = BaseCarrierTariffSheetSource


class AirIndiaTariffSheetSource(BaseCarrierTariffSheetSource):
    """Tier 2 FareSource backed by Air India's DGCA Rule 135(2) tariff sheet."""

    def __init__(
        self,
        use_fixture: bool = True,
        fixture_csv: Optional[Path] = None,
        pdf_path: Optional[Path] = None,
    ) -> None:
        super().__init__(
            carrier_iata="AI",
            source_id="air_india_tariff_v1",
            fixture_csv=fixture_csv or AI_FIXTURE_CSV,
            use_fixture=use_fixture,
            pdf_path=pdf_path,
        )


class AkasaTariffSheetSource(BaseCarrierTariffSheetSource):
    """Tier 2 FareSource backed by Akasa Air's DGCA Rule 135(2) tariff sheet."""

    def __init__(
        self,
        use_fixture: bool = True,
        fixture_csv: Optional[Path] = None,
        pdf_path: Optional[Path] = None,
    ) -> None:
        super().__init__(
            carrier_iata="QP",
            source_id="akasa_tariff_v1",
            fixture_csv=fixture_csv or QP_FIXTURE_CSV,
            use_fixture=use_fixture,
            pdf_path=pdf_path,
        )

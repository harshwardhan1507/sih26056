"""
Tariff-sheet adapter — Tier 2 fare source for APIx.

Legal basis
-----------
Under Sub-Rule (2) of Rule 135 of the Aircraft Rules, 1937, and DGCA Air
Transport Circular 2 of 2010, airlines must publish route-wise tariff sheets
on their websites.  IndiGo publishes at:
  https://www.goindigo.in/information/fare-information.html
  → PDF linked as "IndiGo-Tariff-Sheet-YYYY-MM-DD.pdf"

The tariff sheet lists ONE WAY DIRECT ECONOMY fares per route, with two rows
per route:
  - Maximum: the ceiling price per fare bucket (1–21)
  - Minimum: the floor price per fare bucket (1–21)

Each "fare bucket" corresponds to a group of seats sold at that price band.
The bucket number increases with booking recency (higher bucket ≈ shorter
advance purchase window / higher last-minute fare).

What this adapter provides
--------------------------
``TariffBand`` objects represent one (route, Maximum/Minimum) row from the
sheet.  ``IndiGoTariffSheetSource`` converts the midpoint of the widest
non-None band on a route into a ``FareQuote`` with:
  - collection_method = "tariff_sheet"
  - source_id = "indigo_tariff_v1"
  - quality_flag = "ok"

This populates the resolver's Tier 2 slot.  If parsing fails for any reason,
``get_quotes`` returns ``[]`` and the resolver falls back to Tier 3/4.

Known limitations (documented per issue #11)
--------------------------------------------
| Limitation                        | Impact on quotes                         |
|-----------------------------------|------------------------------------------|
| Band = range, not exact price     | Midpoint used; wide bands reduce precision|
| Base fare only (taxes NOT included)| FareQuote.total_fare_inr = base; note    |
|                                   | states "excl. mandatory taxes/fees"      |
| Route direction not differentiated| Sheet states "v.v." (both directions);   |
|                                   | adapter emits same band for both dirs    |
| Advance window not published      | Window is mapped to a fare BUCKET via    |
|                                   | ADVANCE_WINDOW_TO_BUCKET (stated         |
|                                   | assumption, see that constant)           |
| Constant within a calendar month  | A sheet is republished monthly, so this  |
|                                   | tier contributes no day-to-day price     |
|                                   | signal. It is a level reference and a    |
|                                   | coverage backstop, NOT a daily series.   |
| Declared band, not transacted fare| Values are regulatory floor/ceiling      |
|                                   | midpoints, typically well above the fare |
|                                   | a consumer actually pays                 |
| Only carrier 6E here              | Air India and Akasa live in              |
|                                   | tariff_carriers.py, sharing this logic   |
"""

from __future__ import annotations

import csv
import logging
import re
import urllib.request
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from .base import FareQuote, FareSource

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# Unicode minus used in IndiGo PDF (U+2212), distinct from ASCII hyphen-minus
_PDF_MINUS = "\u2212"

# Source metadata
_SOURCE_ID = "indigo_tariff_v1"
_COLLECTION_METHOD = "tariff_sheet"
_CARRIER_IATA = "6E"  # IndiGo

# Live URL pattern (YYYY-MM-DD suffix changes monthly)
_LIVE_URL_TEMPLATE = (
    "https://www.goindigo.in/content/dam/s6web/in/en/assets/documents/"
    "tariff_sheet/IndiGo-Tariff-Sheet-{date}.pdf"
)

# Committed fixture paths (used when use_fixture=True)
_FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"
FIXTURE_PDF = _FIXTURE_DIR / "IndiGo-Tariff-Sheet-2026-09-01.pdf"
FIXTURE_CSV = _FIXTURE_DIR / "indigo_tariff_basket_rows.csv"

# IATA ↔ IndiGo city-name mapping (as they appear in the PDF)
_CITY_TO_IATA: dict[str, str] = {
    "Delhi": "DEL",
    "Mumbai": "BOM",
    "Bengaluru": "BLR",
    "Kolkata": "CCU",
    "Chennai": "MAA",
    "Hyderabad": "HYD",
    "Goa": "GOI",
}
_IATA_TO_CITY: dict[str, str] = {v: k for k, v in _CITY_TO_IATA.items()}

# Number of fare buckets per row in the IndiGo tariff sheet
_N_FARE_BUCKETS = 21

# ---------------------------------------------------------------------------
# Advance window -> fare bucket
# ---------------------------------------------------------------------------
# The sheet's own semantics (see module docstring): bucket 1 is the cheapest
# inventory and bucket 21 the dearest, with bucket number rising as departure
# approaches. Selecting a bucket by advance window is therefore the only way a
# tariff sheet can express advance-purchase structure at all.
#
# Without this, every advance window returned the SAME number, so 6E/AI/QP
# contributed a price relative of exactly 1.0 on every single day while still
# occupying a slot in the matched sample — silently damping the index.
#
# The specific bucket per window is a STATED ASSUMPTION, not an estimate: the
# sheet does not publish an inventory-to-lead-time map. It is chosen to span
# the published band monotonically. Revisit against booking-curve data.
ADVANCE_WINDOW_TO_BUCKET: dict[int, int] = {
    45: 3,    # early booking -> low inventory bucket
    30: 5,
    15: 8,
    7: 12,
    1: 17,    # last minute -> high inventory bucket
}
_DEFAULT_BUCKET = 8


def bucket_for_window(advance_window_days: int) -> int:
    """1-based fare bucket index used to price a given advance window."""
    return ADVANCE_WINDOW_TO_BUCKET.get(advance_window_days, _DEFAULT_BUCKET)


# ---------------------------------------------------------------------------
# TariffBand dataclass
# ---------------------------------------------------------------------------

@dataclass
class TariffBand:
    """
    One declared fare band row from the IndiGo tariff sheet.

    Attributes
    ----------
    origin_iata, destination_iata:
        IATA codes for the route (sheet states "v.v." so direction is
        interchangeable; we store the direction as read from the PDF).
    row_type:
        ``"Maximum"`` or ``"Minimum"`` — the fare ceiling or floor row.
    distance_km:
        Route distance in km as stated in the tariff sheet.
    fares:
        List of up to 21 fare amounts in INR (``None`` where the PDF has
        ``"NA"``).  Index 0 = Fare-1 (lowest bucket), index 20 = Fare-21.
    min_fare_inr:
        Smallest non-None fare in the ``fares`` list (convenience field).
    max_fare_inr:
        Largest non-None fare in the ``fares`` list (convenience field).
    source_url:
        URL or file path the data was read from.
    retrieved_at_utc:
        When the data was loaded (UTC).
    effective_month:
        ``"YYYY-MM"`` parsed from the PDF filename where available,
        else ``None``.
    notes:
        Free-text limitations note.
    """

    origin_iata: str
    destination_iata: str
    row_type: str                       # "Maximum" | "Minimum"
    distance_km: Optional[int]
    fares: list[Optional[float]]        # length 21
    min_fare_inr: Optional[float]
    max_fare_inr: Optional[float]
    source_url: str
    retrieved_at_utc: datetime
    effective_month: Optional[str]      # "YYYY-MM" | None
    notes: str = "Base fare only. Mandatory taxes and fees are excluded."

    @property
    def route_key(self) -> str:
        """Canonical route key: ``"DEL-BOM"``."""
        return f"{self.origin_iata}-{self.destination_iata}"


# ---------------------------------------------------------------------------
# Parser — pure function, easy to unit-test
# ---------------------------------------------------------------------------

def parse_indigo_tariff_pdf(
    pdf_path: Path,
    source_url: str,
    origin_filter: Optional[set[str]] = None,
    destination_filter: Optional[set[str]] = None,
) -> list[TariffBand]:
    """
    Parse an IndiGo tariff PDF and return ``TariffBand`` objects.

    Parameters
    ----------
    pdf_path:
        Path to the PDF file.
    source_url:
        URL or path to record in provenance fields.
    origin_filter, destination_filter:
        Optional IATA code sets.  If given, only rows matching both filters
        (in either direction) are returned.

    Returns
    -------
    list[TariffBand]
        Empty list if the file cannot be parsed (never raises).
    """
    try:
        import pdfplumber  # optional dependency, imported lazily
    except ImportError as exc:
        # Raise rather than return []. Returning an empty list made a missing
        # dependency indistinguishable from "this route isn't in the sheet":
        # the resolver quietly fell through to the simulator and the run
        # reported 100% simulated data with no visible cause.
        raise RuntimeError(
            "pdfplumber is required to parse live tariff sheet PDFs but is not "
            "installed. Install it with `pip install pdfplumber` (it is listed "
            "in requirements.txt), or use the committed CSV fixture with "
            "use_fixture=True."
        ) from exc

    retrieved_at = datetime.now(timezone.utc)
    effective_month = _extract_effective_month(str(pdf_path))
    bands: list[TariffBand] = []

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page_idx, page in enumerate(pdf.pages):
                try:
                    text = page.extract_text()
                except Exception as exc:
                    logger.debug("Page %d: skipped (%s)", page_idx + 1, exc)
                    continue
                if not text:
                    continue
                for line in text.split("\n"):
                    band = _parse_line(
                        line, source_url, retrieved_at, effective_month,
                        origin_filter, destination_filter,
                    )
                    if band is not None:
                        bands.append(band)
    except Exception as exc:
        logger.warning("Failed to open/parse PDF %s: %s", pdf_path, exc)

    return bands


def parse_indigo_tariff_csv(
    csv_path: Path,
    source_url: str,
) -> list[TariffBand]:
    """
    Parse the pre-extracted fixture CSV (faster, no pdfplumber needed for tests).

    CSV columns: origin_iata, destination_iata, origin_city, destination_city,
    row_type, distance_km, fare_1 … fare_21
    """
    retrieved_at = datetime.now(timezone.utc)
    effective_month = (
        _extract_effective_month(str(csv_path))
        or _extract_effective_month(source_url)
        or _extract_effective_month(str(FIXTURE_PDF))
    )
    bands: list[TariffBand] = []

    with open(csv_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            fares: list[Optional[float]] = []
            for i in range(1, _N_FARE_BUCKETS + 1):
                val = row.get(f"fare_{i}", "")
                if val == "" or val is None:
                    fares.append(None)
                else:
                    try:
                        fares.append(float(val))
                    except ValueError:
                        fares.append(None)
            valid = [f for f in fares if f is not None]
            bands.append(TariffBand(
                origin_iata=row["origin_iata"],
                destination_iata=row["destination_iata"],
                row_type=row["row_type"],
                distance_km=int(row["distance_km"]) if row.get("distance_km") else None,
                fares=fares,
                min_fare_inr=min(valid) if valid else None,
                max_fare_inr=max(valid) if valid else None,
                source_url=source_url,
                retrieved_at_utc=retrieved_at,
                effective_month=effective_month,
            ))
    return bands


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _extract_effective_month(path_str: str) -> Optional[str]:
    """Extract YYYY-MM from a filename like 'IndiGo-Tariff-Sheet-2026-09-01.pdf'."""
    m = re.search(r"(\d{4}-\d{2})-\d{2}", path_str)
    return m.group(1) if m else None


def _parse_line(
    line: str,
    source_url: str,
    retrieved_at: datetime,
    effective_month: Optional[str],
    origin_filter: Optional[set[str]],
    destination_filter: Optional[set[str]],
) -> Optional[TariffBand]:
    """Parse one text line from the PDF. Returns None if the line is not a data row."""
    if _PDF_MINUS not in line:
        return None
    parts = line.strip().split()
    try:
        minus_idx = parts.index(_PDF_MINUS)
    except ValueError:
        return None

    if minus_idx < 1 or minus_idx + 3 >= len(parts):
        return None

    city1 = parts[minus_idx - 1]
    city2 = parts[minus_idx + 1]
    iata1 = _CITY_TO_IATA.get(city1)
    iata2 = _CITY_TO_IATA.get(city2)
    if iata1 is None or iata2 is None:
        return None

    # Apply filters (both directions count)
    if origin_filter and iata1 not in origin_filter and iata2 not in origin_filter:
        return None
    if destination_filter and iata2 not in destination_filter and iata1 not in destination_filter:
        return None

    rest = parts[minus_idx + 2:]
    if not rest:
        return None
    row_type = rest[0]
    if row_type not in ("Maximum", "Minimum"):
        return None

    try:
        distance_km: Optional[int] = int(rest[1]) if len(rest) > 1 and rest[1].isdigit() else None
    except (ValueError, IndexError):
        distance_km = None

    fare_start = 2
    fares: list[Optional[float]] = []
    for token in rest[fare_start: fare_start + _N_FARE_BUCKETS]:
        if token == "NA":
            fares.append(None)
        else:
            try:
                fares.append(float(token.replace(",", "")))
            except ValueError:
                fares.append(None)

    # Pad to 21 if short
    while len(fares) < _N_FARE_BUCKETS:
        fares.append(None)

    valid = [f for f in fares if f is not None]
    return TariffBand(
        origin_iata=iata1,
        destination_iata=iata2,
        row_type=row_type,
        distance_km=distance_km,
        fares=fares,
        min_fare_inr=min(valid) if valid else None,
        max_fare_inr=max(valid) if valid else None,
        source_url=source_url,
        retrieved_at_utc=retrieved_at,
        effective_month=effective_month,
    )


# ---------------------------------------------------------------------------
# FareSource adapter
# ---------------------------------------------------------------------------

def find_band(
    bands: list[TariffBand],
    origin: str,
    destination: str,
    row_type: str,
) -> Optional[TariffBand]:
    """
    Locate one route row of the requested type, in either direction.

    Tariff sheets state routes as "v.v." (both directions), so a reverse match
    is a legitimate hit rather than a fallback.
    """
    orig = origin.strip().upper()
    dest = destination.strip().upper()
    for band in bands:
        if band.row_type != row_type:
            continue
        if (
            (band.origin_iata == orig and band.destination_iata == dest)
            or (band.origin_iata == dest and band.destination_iata == orig)
        ):
            return band
    return None


def band_fare_for_window(
    bands: list[TariffBand],
    origin: str,
    destination: str,
    advance_window_days: int,
) -> Optional[float]:
    """
    Representative declared fare for a (route, advance window) from a tariff sheet.

    Takes the midpoint of the Minimum-row and Maximum-row fares AT THE BUCKET
    corresponding to the advance window. The published band is a permitted
    range, so its midpoint is the neutral point estimate within it.

    This is the single definition shared by every carrier adapter. Previously
    the IndiGo adapter used the Minimum row's overall floor while the Air
    India / Akasa adapters used the Maximum row's overall midpoint, which put
    carriers on different price definitions inside the same matched sample and
    showed up as a spurious level difference between them.

    Returns None when the route is not in the sheet or the bucket is blank.
    """
    max_band = find_band(bands, origin, destination, "Maximum")
    min_band = find_band(bands, origin, destination, "Minimum")
    if max_band is None and min_band is None:
        return None

    idx = bucket_for_window(advance_window_days) - 1

    def _at(band: Optional[TariffBand]) -> Optional[float]:
        if band is None or idx >= len(band.fares):
            return None
        return band.fares[idx]

    hi = _at(max_band)
    lo = _at(min_band)

    # Blank buckets are common ("NA" in the PDF). Fall back along the row to
    # the nearest populated bucket rather than dropping the route entirely.
    if hi is None and max_band is not None:
        hi = _nearest_populated(max_band.fares, idx)
    if lo is None and min_band is not None:
        lo = _nearest_populated(min_band.fares, idx)

    if lo is not None and hi is not None:
        return (lo + hi) / 2.0 if hi >= lo else (hi + lo) / 2.0
    return hi if hi is not None else lo


def _nearest_populated(fares: list[Optional[float]], idx: int) -> Optional[float]:
    """Nearest non-empty bucket to ``idx``, searching outward in both directions."""
    for offset in range(1, len(fares)):
        for probe in (idx - offset, idx + offset):
            if 0 <= probe < len(fares) and fares[probe] is not None:
                return fares[probe]
    return None


class IndiGoTariffSheetSource(FareSource):
    """
    Tier 2 FareSource backed by IndiGo's DGCA-mandated tariff sheet.

    Usage
    -----
    # Use pre-committed CSV fixture (no network, no pdfplumber):
    src = IndiGoTariffSheetSource(use_fixture=True)

    # Use live PDF (downloads on first call, caches in memory):
    src = IndiGoTariffSheetSource(use_fixture=False, tariff_date="2026-09-01")

    The adapter converts bands to FareQuote objects by taking the midpoint of
    the ``[min_fare_inr, max_fare_inr]`` band for the matched route.  If no
    band is found for the requested route, ``[]`` is returned (resolver
    continues to Tier 3/4).

    If any parsing or fetch error occurs, ``[]`` is returned and a warning is
    logged — the adapter never propagates exceptions (per issue #11 acceptance
    criterion: "adapter does not break daily quote collection if tariff parsing
    fails").
    """

    source_id = _SOURCE_ID
    collection_method = _COLLECTION_METHOD

    def __init__(
        self,
        use_fixture: bool = True,
        tariff_date: Optional[str] = None,
        fixture_csv: Optional[Path] = None,
    ) -> None:
        """
        Parameters
        ----------
        use_fixture:
            If True, load from the pre-committed CSV fixture (default).
            If False, download/parse the live PDF.
        tariff_date:
            ``"YYYY-MM-DD"`` for the live PDF URL.  Defaults to the 1st of
            the current month.
        fixture_csv:
            Override path to the fixture CSV (used in tests).
        """
        self._use_fixture = use_fixture
        self._tariff_date = tariff_date
        self._fixture_csv = Path(fixture_csv) if fixture_csv else FIXTURE_CSV
        self._bands_cache: Optional[list[TariffBand]] = None

    # ------------------------------------------------------------------
    # FareSource interface
    # ------------------------------------------------------------------

    def get_quotes(
        self,
        origin: str,
        destination: str,
        as_of_date: date,
        advance_window_days: int,
        carriers: list[str],
    ) -> list[FareQuote]:
        """
        Return a FareQuote for IndiGo (6E) if this route appears in the
        tariff sheet.  Returns [] if the carrier list doesn't include 6E,
        if the route has no band, or if any error occurs.
        """
        normalized = [c.strip().upper() for c in carriers]
        if _CARRIER_IATA not in normalized:
            return []

        try:
            bands = self._get_bands()
        except Exception as exc:
            logger.warning("%s: failed to load bands: %s", self.source_id, exc)
            return []

        fare = band_fare_for_window(bands, origin, destination, advance_window_days)
        if fare is None:
            # Route not in tariff sheet — resolver falls back
            return []

        return [
            FareQuote(
                collected_at_utc=datetime.now(timezone.utc),
                # The flight quoted today departs advance_window_days later.
                departure_date=as_of_date + timedelta(days=advance_window_days),
                advance_window_days=advance_window_days,
                origin_iata=origin.strip().upper(),
                destination_iata=destination.strip().upper(),
                carrier_iata=_CARRIER_IATA,
                fare_class="Economy",
                total_fare_inr=round(fare, 2),
                source_id=self.source_id,
                collection_method=self.collection_method,
                quality_flag="ok",
            )
        ]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_bands(self) -> list[TariffBand]:
        """Load and cache bands from the fixture or live PDF."""
        if self._bands_cache is not None:
            return self._bands_cache

        if self._use_fixture:
            if not self._fixture_csv.exists():
                raise FileNotFoundError(
                    f"Fixture CSV not found: {self._fixture_csv}\n"
                    "Run scripts/extract_indigo_tariff_fixture.py to regenerate it."
                )
            self._bands_cache = parse_indigo_tariff_csv(
                self._fixture_csv,
                source_url=str(self._fixture_csv),
            )
        else:
            tariff_date = self._tariff_date or _default_tariff_date()
            url = _LIVE_URL_TEMPLATE.format(date=tariff_date)
            pdf_path = self._download_pdf(url)
            self._bands_cache = parse_indigo_tariff_pdf(
                pdf_path,
                source_url=url,
            )

        return self._bands_cache

    @staticmethod
    def _find_band(
        bands: list[TariffBand],
        origin: str,
        destination: str,
    ) -> Optional[TariffBand]:
        """
        Return the Minimum-row band for a route (either direction).
        Falls back to Maximum-row if no Minimum row found.
        The Minimum row gives the floor price, which is the more
        conservative (closer to consumer-paid) estimate.
        """
        # Prefer Minimum row
        for row_type_pref in ("Minimum", "Maximum"):
            for band in bands:
                if band.row_type != row_type_pref:
                    continue
                if (
                    (band.origin_iata == origin and band.destination_iata == destination)
                    or (band.origin_iata == destination and band.destination_iata == origin)
                ):
                    return band
        return None

    @staticmethod
    def _band_midpoint(band: TariffBand) -> Optional[float]:
        """Midpoint of the overall [min_fare_inr, max_fare_inr] range."""
        lo, hi = band.min_fare_inr, band.max_fare_inr
        if lo is None and hi is None:
            return None
        if lo is None:
            return hi
        if hi is None:
            return lo
        return (lo + hi) / 2.0

    @staticmethod
    def _download_pdf(url: str) -> Path:
        """Download the live PDF to a temporary path and return it."""
        dest = _FIXTURE_DIR / f"_live_{Path(url).name}"
        dest.parent.mkdir(parents=True, exist_ok=True)
        logger.info("Downloading IndiGo tariff sheet: %s", url)
        try:
            urllib.request.urlretrieve(url, dest)
        except Exception as exc:
            raise RuntimeError(f"Failed to download tariff PDF from {url}: {exc}") from exc
        return dest


def _default_tariff_date() -> str:
    """Return the 1st of the current month as YYYY-MM-DD."""
    today = datetime.now(timezone.utc)
    return f"{today.year}-{today.month:02d}-01"

"""
Isolated data access layer for APIx FastAPI endpoints.

Dataset selection
-----------------
The API serves the LIVE collection log
(``data/raw/live_collection/fare_quote_log.csv``) when it exists, and falls
back to the simulated demo artifact (``apix/data/fare_quote.csv``) otherwise.
Whichever it serves, every response reports which one and what share of the
rows are simulated.

This used to read only the demo file, so ``/sources/status`` reported
``fallback_simulated_percentage: 100.0`` while the daily collection clock's
output -- 60% of it from real DGCA tariff sheets -- was never exposed
anywhere. Two disconnected data planes, with the dashboard wired to the
wrong one.

Graceful degradation:
  - Missing route weights fall back to placeholder weights, source="placeholder"
  - No quote data at all raises DataUnavailableError (HTTP 503)
  - /sources/status and /quality return 200 with zero counts when empty
"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from apix.index.elementary import build_elementary_index
from .errors import DataUnavailableError
from .schemas import (
    AggregateIndexPointOut,
    AggregateIndexResponse,
    DatasetProvenanceOut,
    ElementaryIndexPointOut,
    ElementaryIndexResponse,
    QualityStatusOut,
    QuoteOut,
    QuotesResponse,
    RouteBasketOut,
    RouteItemOut,
    RouteSummaryOut,
    RouteSummaryResponse,
    SourceStatusOut,
)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
LIVE_COLLECTION_CSV = PROJECT_ROOT / "data" / "raw" / "live_collection" / "fare_quote_log.csv"

ADVANCE_WINDOWS = (1, 7, 15, 30, 45)

# Hardcoded placeholder fallback if route_weights.json does not exist
PLACEHOLDER_ROUTE_WEIGHTS: Dict[str, float] = {
    "DEL-BOM": 0.20, "DEL-BLR": 0.14, "DEL-CCU": 0.09,
    "DEL-MAA": 0.09, "DEL-HYD": 0.10, "BOM-BLR": 0.10,
    "BOM-MAA": 0.08, "BOM-CCU": 0.05, "BLR-HYD": 0.06,
    "BLR-MAA": 0.04, "DEL-GOI": 0.03, "BOM-GOI": 0.02,
}

# Methods that represent data actually observed from a source, as opposed to
# generated or filled in.
_OBSERVED_METHODS = {"api", "tariff_sheet", "scrape", "historical_panel"}


@dataclass(frozen=True)
class QuoteRecord:
    """One parsed quote row, with its observation date resolved."""
    observation_date: date
    departure_date: date
    advance_window_days: int
    origin_iata: str
    destination_iata: str
    carrier_iata: str
    fare_class: str
    total_fare_inr: Optional[float]
    source_id: str
    collection_method: str
    quality_flag: str
    collected_at_utc: datetime


@dataclass(frozen=True)
class Dataset:
    """The quote set currently being served, plus its provenance."""
    path: Path
    records: List[QuoteRecord]
    is_live_collection: bool

    @property
    def simulated_count(self) -> int:
        return sum(1 for r in self.records if r.collection_method == "simulated")

    @property
    def observed_count(self) -> int:
        return sum(1 for r in self.records if r.collection_method in _OBSERVED_METHODS)

    @property
    def simulated_pct(self) -> float:
        if not self.records:
            return 0.0
        return round(self.simulated_count / len(self.records) * 100, 2)

    @property
    def dataset_type(self) -> str:
        """'production' | 'mixed' | 'synthetic' — stated, never assumed."""
        if not self.records:
            return "synthetic"
        if self.simulated_count == 0:
            return "production"
        if self.simulated_count == len(self.records):
            return "synthetic"
        return "mixed"

    def provenance(self) -> DatasetProvenanceOut:
        return DatasetProvenanceOut(
            dataset_type=self.dataset_type,
            source_file=self.path.name,
            is_live_collection=self.is_live_collection,
            total_quotes=len(self.records),
            observed_quotes=self.observed_count,
            simulated_quotes=self.simulated_count,
            simulated_percentage=self.simulated_pct,
            note=(
                "Serving the live collection log."
                if self.is_live_collection
                else "Serving the simulated backfill demo; no live collection data present."
            ),
        )


def _resolve_data_dir(data_dir: Optional[Path]) -> Path:
    return data_dir if data_dir is not None else DEFAULT_DATA_DIR


def _parse_float(raw: Optional[str]) -> Optional[float]:
    if raw is None or raw.strip() in ("", "None", "null", "NA"):
        return None
    try:
        return float(raw)
    except ValueError:
        return None


def _parse_row(row: dict) -> Optional[QuoteRecord]:
    """Parse one CSV row, or None if it cannot be trusted."""
    try:
        window = int(row["advance_window_days"])
        departure = date.fromisoformat(row["departure_date"].strip())
    except (KeyError, ValueError, AttributeError):
        return None

    # observation_date is written by the collectors; derive it for older files.
    raw_obs = (row.get("observation_date") or "").strip()
    try:
        observation = date.fromisoformat(raw_obs) if raw_obs else departure - timedelta(days=window)
    except ValueError:
        observation = departure - timedelta(days=window)

    raw_collected = (row.get("collected_at_utc") or "").strip()
    try:
        collected = datetime.fromisoformat(raw_collected)
    except ValueError:
        return None

    return QuoteRecord(
        observation_date=observation,
        departure_date=departure,
        advance_window_days=window,
        origin_iata=row.get("origin_iata", "").strip().upper(),
        destination_iata=row.get("destination_iata", "").strip().upper(),
        carrier_iata=row.get("carrier_iata", "").strip().upper(),
        fare_class=(row.get("fare_class") or "Economy").strip(),
        total_fare_inr=_parse_float(row.get("total_fare_inr")),
        source_id=(row.get("source_id") or "unknown").strip(),
        collection_method=(row.get("collection_method") or "unknown").strip().lower(),
        quality_flag=(row.get("quality_flag") or "ok").strip().lower(),
        collected_at_utc=collected,
    )


def load_dataset(data_dir: Optional[Path] = None) -> Dataset:
    """
    Load the quote set to serve: live collection if present, else the demo.

    Raises DataUnavailableError when neither exists.
    """
    directory = _resolve_data_dir(data_dir)
    demo_csv = directory / "fare_quote.csv"

    candidates: List[Tuple[Path, bool]] = []
    if data_dir is None and LIVE_COLLECTION_CSV.is_file():
        candidates.append((LIVE_COLLECTION_CSV, True))
    if demo_csv.is_file():
        candidates.append((demo_csv, False))

    for path, is_live in candidates:
        with open(path, "r", encoding="utf-8", newline="") as f:
            records = [r for r in (_parse_row(row) for row in csv.DictReader(f)) if r]
        if records:
            return Dataset(path=path, records=records, is_live_collection=is_live)

    raise DataUnavailableError(
        detail=(
            "No fare quote data available. Run `py apix/backfill_demo.py` for the "
            "simulated demo, or `py scripts/run_daily_collection.py` to collect."
        ),
        error_code="data_unavailable",
        status_code=503,
    )


def get_routes(data_dir: Optional[Path] = None) -> RouteBasketOut:
    """Route basket with weights and provenance."""
    directory = _resolve_data_dir(data_dir)
    weights_path = directory / "route_weights.json"

    if weights_path.is_file():
        with open(weights_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        raw_weights: Dict[str, float] = payload.get("weights", {})
        routes = [
            RouteItemOut(
                route_id=r_id,
                origin=r_id.split("-")[0],
                destination=r_id.split("-")[1],
                weight=round(float(w), 6),
            )
            for r_id, w in raw_weights.items()
        ]
        return RouteBasketOut(
            source=payload.get("source", "unknown"),
            coverage_month=payload.get("coverage_month"),
            generated_date=payload.get("generated_date"),
            total_basket_pax=payload.get("total_basket_pax"),
            basket_share_of_domestic_pct=payload.get("basket_share_of_domestic_pct"),
            routes=routes,
        )

    routes = [
        RouteItemOut(
            route_id=r_id,
            origin=r_id.split("-")[0],
            destination=r_id.split("-")[1],
            weight=round(w, 6),
        )
        for r_id, w in PLACEHOLDER_ROUTE_WEIGHTS.items()
    ]
    return RouteBasketOut(
        source="placeholder",
        coverage_month=None,
        generated_date=None,
        total_basket_pax=None,
        basket_share_of_domestic_pct=None,
        routes=routes,
    )


def get_quotes(
    data_dir: Optional[Path] = None,
    origin: Optional[str] = None,
    destination: Optional[str] = None,
    advance_window_days: Optional[int] = None,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    limit: Optional[int] = None,
) -> QuotesResponse:
    """Filtered fare quotes (filters are ANDed). Dates filter on observation date."""
    dataset = load_dataset(data_dir)

    target_orig = origin.strip().upper() if origin else None
    target_dest = destination.strip().upper() if destination else None

    matched = [
        r for r in dataset.records
        if (target_orig is None or r.origin_iata == target_orig)
        and (target_dest is None or r.destination_iata == target_dest)
        and (advance_window_days is None or r.advance_window_days == advance_window_days)
        and (date_from is None or r.observation_date >= date_from)
        and (date_to is None or r.observation_date <= date_to)
    ]
    matched.sort(key=lambda r: (r.observation_date, r.origin_iata, r.destination_iata,
                                r.advance_window_days, r.carrier_iata))

    total = len(matched)
    if limit is not None and limit > 0:
        matched = matched[:limit]

    return QuotesResponse(
        count=len(matched),
        total_matched=total,
        provenance=dataset.provenance(),
        quotes=[
            QuoteOut(
                collected_at_utc=r.collected_at_utc,
                observation_date=r.observation_date,
                departure_date=r.departure_date,
                advance_window_days=r.advance_window_days,
                origin_iata=r.origin_iata,
                destination_iata=r.destination_iata,
                carrier_iata=r.carrier_iata,
                fare_class=r.fare_class,
                total_fare_inr=r.total_fare_inr,
                source_id=r.source_id,
                collection_method=r.collection_method,
                quality_flag=r.quality_flag,
            )
            for r in matched
        ],
    )


def _daily_prices(
    records: List[QuoteRecord],
    origin: str,
    destination: str,
    advance_window_days: int,
) -> Tuple[List[date], List[Dict[str, float]]]:
    """
    Build a dense (calendar, prices-per-day) series for one stratum.

    Grouping is on OBSERVATION date, and duplicate carrier rows for the same
    day are resolved by preferring the higher-trust collection method, then the
    later collection timestamp. The previous implementation grouped on
    departure date and let the last CSV row silently win, so a double-run of
    the collector changed the index depending on file order.
    """
    best: Dict[Tuple[date, str], QuoteRecord] = {}
    for r in records:
        if r.origin_iata != origin or r.destination_iata != destination:
            continue
        if r.advance_window_days != advance_window_days:
            continue
        if r.quality_flag == "outlier":
            continue
        if r.total_fare_inr is None or r.total_fare_inr <= 0:
            continue

        key = (r.observation_date, r.carrier_iata)
        incumbent = best.get(key)
        if incumbent is None or _precedence(r) > _precedence(incumbent):
            best[key] = r

    if not best:
        return [], []

    days = sorted({k[0] for k in best})
    # Dense calendar so gaps stay visible instead of collapsing.
    calendar = [days[0] + timedelta(days=i) for i in range((days[-1] - days[0]).days + 1)]

    series: List[Dict[str, float]] = []
    for day in calendar:
        series.append({
            carrier: rec.total_fare_inr
            for (d, carrier), rec in best.items()
            if d == day and rec.total_fare_inr is not None
        })
    return calendar, series


_METHOD_TRUST = {
    "api": 5, "tariff_sheet": 4, "scrape": 3,
    "historical_panel": 2, "simulated": 1, "imputed": 0,
}


def _precedence(record: QuoteRecord) -> Tuple[int, datetime]:
    return (_METHOD_TRUST.get(record.collection_method, -1), record.collected_at_utc)


def get_elementary_index(
    origin: str,
    destination: str,
    advance_window_days: int,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    data_dir: Optional[Path] = None,
) -> ElementaryIndexResponse:
    """Chained matched-sample Jevons index for one (route, advance window)."""
    dataset = load_dataset(data_dir)
    orig = origin.strip().upper()
    dest = destination.strip().upper()

    records = [
        r for r in dataset.records
        if (date_from is None or r.observation_date >= date_from)
        and (date_to is None or r.observation_date <= date_to)
    ]

    calendar, daily = _daily_prices(records, orig, dest, advance_window_days)
    if not calendar:
        return ElementaryIndexResponse(
            origin=orig, destination=dest,
            advance_window_days=advance_window_days,
            base_value=100.0, series_length=0, series=[],
            provenance=dataset.provenance(),
        )

    values = build_elementary_index(daily, base_value=100.0)
    return ElementaryIndexResponse(
        origin=orig,
        destination=dest,
        advance_window_days=advance_window_days,
        base_value=100.0,
        series_length=len(values),
        provenance=dataset.provenance(),
        series=[
            ElementaryIndexPointOut(
                day=idx,
                date=calendar[idx],
                index_value=round(val, 3),
                carrier_count=len(daily[idx]),
            )
            for idx, val in enumerate(values)
        ],
    )


def get_aggregate_index(data_dir: Optional[Path] = None) -> AggregateIndexResponse:
    """The headline aggregate index series from index_series.csv."""
    directory = _resolve_data_dir(data_dir)
    csv_path = directory / "index_series.csv"

    if not csv_path.is_file():
        raise DataUnavailableError(
            detail=(
                "index_series.csv is not available. Run `py apix/backfill_demo.py` "
                "to generate it."
            ),
            error_code="data_unavailable",
            status_code=503,
        )

    points: List[AggregateIndexPointOut] = []
    methodology = "unknown"
    dataset_type = "unknown"

    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            try:
                day_val = int(row["day"])
                val = float(row["APIx_aggregate"])
            except (KeyError, ValueError):
                continue
            methodology = row.get("methodology", methodology) or methodology
            dataset_type = row.get("dataset_type", dataset_type) or dataset_type

            raw_date = (row.get("date") or "").strip()
            try:
                point_date = date.fromisoformat(raw_date) if raw_date else None
            except ValueError:
                point_date = None

            change = _parse_float(row.get("change_pct"))
            points.append(AggregateIndexPointOut(
                day=day_val,
                date=point_date,
                index_value=round(val, 3),
                change_pct=round(change, 3) if change is not None else None,
            ))

    return AggregateIndexResponse(
        base_value=100.0,
        series_length=len(points),
        methodology=methodology,
        dataset_type=dataset_type,
        series=points,
    )


def get_route_summaries(data_dir: Optional[Path] = None) -> RouteSummaryResponse:
    """
    Per-route index, average fare and coverage, computed from the served data.

    Exists because the dashboard needs these figures and had been filling them
    with hardcoded constants -- the same 103.5 index, 2.1% change, INR 6,500
    fare and identical sparkline on all twelve routes.
    """
    dataset = load_dataset(data_dir)
    basket = get_routes(data_dir)

    summaries: List[RouteSummaryOut] = []
    for item in basket.routes:
        per_window_series: List[List[float]] = []
        fares: List[float] = []
        observations = 0

        for window in ADVANCE_WINDOWS:
            calendar, daily = _daily_prices(
                dataset.records, item.origin, item.destination, window
            )
            if not calendar:
                continue
            per_window_series.append(build_elementary_index(daily, base_value=100.0))
            observations += sum(len(day) for day in daily)
            if daily and daily[-1]:
                fares.extend(daily[-1].values())

        if not per_window_series:
            summaries.append(RouteSummaryOut(
                route_id=item.route_id, origin=item.origin, destination=item.destination,
                weight=item.weight, current_index=None, change_pct=None,
                average_fare=None, matched_observations=0,
                coverage_status="insufficient", series_length=0, sparkline=[],
            ))
            continue

        length = min(len(s) for s in per_window_series)
        combined = [
            sum(s[i] for s in per_window_series) / len(per_window_series)
            for i in range(length)
        ]

        current = round(combined[-1], 3)
        change = (
            round((combined[-1] - combined[-2]) / combined[-2] * 100, 3)
            if length > 1 and combined[-2] else None
        )
        # Down-sample to at most 30 points so the payload stays small.
        step = max(1, length // 30)
        sparkline = [round(v, 3) for v in combined[::step]]

        summaries.append(RouteSummaryOut(
            route_id=item.route_id,
            origin=item.origin,
            destination=item.destination,
            weight=item.weight,
            current_index=current,
            change_pct=change,
            average_fare=round(sum(fares) / len(fares)) if fares else None,
            matched_observations=observations,
            coverage_status=(
                "complete" if length >= 30 else "partial" if length > 1 else "insufficient"
            ),
            series_length=length,
            sparkline=sparkline,
        ))

    return RouteSummaryResponse(
        count=len(summaries),
        provenance=dataset.provenance(),
        routes=summaries,
    )


def get_source_status(data_dir: Optional[Path] = None) -> SourceStatusOut:
    """Collection-method distribution and simulated fallback rate."""
    try:
        dataset = load_dataset(data_dir)
    except DataUnavailableError:
        return SourceStatusOut(
            total_quotes=0, by_method={}, by_source_id={},
            fallback_simulated_percentage=0.0,
            provenance=None,
            status_note="No collection data available.",
        )

    by_method: Dict[str, int] = {}
    by_source: Dict[str, int] = {}
    for r in dataset.records:
        by_method[r.collection_method] = by_method.get(r.collection_method, 0) + 1
        by_source[r.source_id] = by_source.get(r.source_id, 0) + 1

    return SourceStatusOut(
        total_quotes=len(dataset.records),
        by_method=by_method,
        by_source_id=by_source,
        fallback_simulated_percentage=dataset.simulated_pct,
        provenance=dataset.provenance(),
        status_note=(
            f"Counted from {dataset.path.name}. Only source identifiers that "
            "actually produced rows are listed; sources with no integration are "
            "absent rather than reported as healthy."
        ),
    )


def get_quality_status(data_dir: Optional[Path] = None) -> QualityStatusOut:
    """Data hygiene metrics by quality flag."""
    try:
        dataset = load_dataset(data_dir)
    except DataUnavailableError:
        return QualityStatusOut(
            total_quotes=0, by_quality_flag={}, ok_count=0,
            sold_out_count=0, outlier_count=0, imputed_count=0,
            quality_score=0.0, provenance=None,
        )

    by_flag: Dict[str, int] = {}
    for r in dataset.records:
        by_flag[r.quality_flag] = by_flag.get(r.quality_flag, 0) + 1

    total = len(dataset.records)
    ok = by_flag.get("ok", 0)
    return QualityStatusOut(
        total_quotes=total,
        by_quality_flag=by_flag,
        ok_count=ok,
        sold_out_count=by_flag.get("sold_out", 0),
        outlier_count=by_flag.get("outlier", 0),
        imputed_count=by_flag.get("imputed", 0),
        quality_score=round(ok / total * 100, 2) if total else 0.0,
        provenance=dataset.provenance(),
    )

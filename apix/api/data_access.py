"""
Isolated data access layer for APIx FastAPI endpoints.

Reads data from local CSV and JSON artifacts in `apix/data/`.
Guarantees graceful degradation:
  - Missing route weights file falls back to placeholder weights with "source": "placeholder"
  - Missing fare_quote.csv or index_series.csv raises DataUnavailableError (HTTP 503)
  - Missing or empty data for /sources/status and /quality returns 200 with zero counts
"""

from __future__ import annotations

import csv
import json
from datetime import date, datetime
from pathlib import Path
from typing import Dict, List, Optional

from apix.index.elementary import build_elementary_index
from .errors import DataUnavailableError
from .schemas import (
    AggregateIndexPointOut,
    AggregateIndexResponse,
    ElementaryIndexPointOut,
    ElementaryIndexResponse,
    QualityStatusOut,
    QuoteOut,
    QuotesResponse,
    RouteBasketOut,
    RouteItemOut,
    SourceStatusOut,
)

DEFAULT_DATA_DIR = Path(__file__).resolve().parent.parent / "data"

# Hardcoded placeholder fallback if route_weights.json does not exist
PLACEHOLDER_ROUTE_WEIGHTS: Dict[str, float] = {
    "DEL-BOM": 0.20, "DEL-BLR": 0.14, "DEL-CCU": 0.09,
    "DEL-MAA": 0.09, "DEL-HYD": 0.10, "BOM-BLR": 0.10,
    "BOM-MAA": 0.08, "BOM-CCU": 0.05, "BLR-HYD": 0.06,
    "BLR-MAA": 0.04, "DEL-GOI": 0.03, "BOM-GOI": 0.02,
}


def _resolve_data_dir(data_dir: Optional[Path]) -> Path:
    return data_dir if data_dir is not None else DEFAULT_DATA_DIR


def get_routes(data_dir: Optional[Path] = None) -> RouteBasketOut:
    """
    Load route basket with weights and provenance.
    If route_weights.json is absent, falls back to placeholder weights with source="placeholder".
    """
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
            source=payload.get("source", "Vonter/india-aviation-traffic (ODbL-1.0)"),
            coverage_month=payload.get("coverage_month"),
            generated_date=payload.get("generated_date"),
            total_basket_pax=payload.get("total_basket_pax"),
            routes=routes,
        )

    # Fallback to placeholder weights
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
    """
    Read fare quotes from fare_quote.csv with optional filters (ANDed together).
    Raises DataUnavailableError if fare_quote.csv is missing.
    """
    directory = _resolve_data_dir(data_dir)
    csv_path = directory / "fare_quote.csv"

    if not csv_path.is_file():
        raise DataUnavailableError(
            detail="Required data file 'fare_quote.csv' is not available.",
            error_code="data_unavailable",
            status_code=503,
        )

    target_orig = origin.strip().upper() if origin else None
    target_dest = destination.strip().upper() if destination else None

    results: List[QuoteOut] = []

    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Filter origin
            if target_orig and row["origin_iata"].strip().upper() != target_orig:
                continue
            # Filter destination
            if target_dest and row["destination_iata"].strip().upper() != target_dest:
                continue
            # Filter advance window
            if advance_window_days is not None:
                try:
                    if int(row["advance_window_days"]) != advance_window_days:
                        continue
                except (ValueError, TypeError):
                    continue

            # Parse departure date
            try:
                dep_date = date.fromisoformat(row["departure_date"].strip())
            except (ValueError, KeyError):
                continue

            # Filter date range
            if date_from and dep_date < date_from:
                continue
            if date_to and dep_date > date_to:
                continue

            # Parse total_fare_inr
            raw_fare = row.get("total_fare_inr")
            if raw_fare is None or raw_fare.strip() in ("", "None", "null"):
                fare = None
            else:
                try:
                    fare = float(raw_fare)
                except ValueError:
                    fare = None

            # Parse collected_at_utc
            try:
                col_at = datetime.fromisoformat(row["collected_at_utc"].strip())
            except (ValueError, KeyError):
                continue

            results.append(
                QuoteOut(
                    collected_at_utc=col_at,
                    departure_date=dep_date,
                    advance_window_days=int(row["advance_window_days"]),
                    origin_iata=row["origin_iata"].strip().upper(),
                    destination_iata=row["destination_iata"].strip().upper(),
                    carrier_iata=row["carrier_iata"].strip().upper(),
                    fare_class=row.get("fare_class", "Economy").strip(),
                    total_fare_inr=fare,
                    source_id=row.get("source_id", "unknown").strip(),
                    collection_method=row.get("collection_method", "unknown").strip(),
                    quality_flag=row.get("quality_flag", "ok").strip(),
                )
            )
            if limit is not None and len(results) >= limit:
                break

    return QuotesResponse(count=len(results), quotes=results)


def get_aggregate_index(data_dir: Optional[Path] = None) -> AggregateIndexResponse:
    """
    Read the chained Laspeyres aggregate index series from index_series.csv.
    Raises DataUnavailableError if index_series.csv is missing.
    """
    directory = _resolve_data_dir(data_dir)
    csv_path = directory / "index_series.csv"

    if not csv_path.is_file():
        raise DataUnavailableError(
            detail="Required data file 'index_series.csv' is not available.",
            error_code="data_unavailable",
            status_code=503,
        )

    points: List[AggregateIndexPointOut] = []
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                day_val = int(row["day"])
                val = float(row["APIx_aggregate"])
                points.append(AggregateIndexPointOut(day=day_val, index_value=round(val, 3)))
            except (KeyError, ValueError):
                continue

    return AggregateIndexResponse(
        base_value=100.0,
        series_length=len(points),
        series=points,
    )


def get_elementary_index(
    origin: str,
    destination: str,
    advance_window_days: int,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    data_dir: Optional[Path] = None,
) -> ElementaryIndexResponse:
    """
    Compute or extract elementary Jevons index for a specific (origin, destination, window)
    market segment from fare_quote.csv.
    """
    directory = _resolve_data_dir(data_dir)
    csv_path = directory / "fare_quote.csv"

    if not csv_path.is_file():
        raise DataUnavailableError(
            detail="Required data file 'fare_quote.csv' is not available to compute elementary index.",
            error_code="data_unavailable",
            status_code=503,
        )

    target_orig = origin.strip().upper()
    target_dest = destination.strip().upper()

    # Group by departure_date -> {carrier_iata: price}
    daily_groups: Dict[date, Dict[str, float]] = {}

    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["origin_iata"].strip().upper() != target_orig:
                continue
            if row["destination_iata"].strip().upper() != target_dest:
                continue
            try:
                if int(row["advance_window_days"]) != advance_window_days:
                    continue
                dep_date = date.fromisoformat(row["departure_date"].strip())
            except (ValueError, KeyError):
                continue

            if date_from and dep_date < date_from:
                continue
            if date_to and dep_date > date_to:
                continue

            # Exclude flagged outliers from elementary price relatives
            quality_flag = row.get("quality_flag", "ok").strip().lower()
            if quality_flag == "outlier":
                continue

            raw_fare = row.get("total_fare_inr")
            if raw_fare and raw_fare.strip() not in ("", "None", "null"):
                try:
                    price = float(raw_fare)
                    carrier = row["carrier_iata"].strip().upper()
                    daily_groups.setdefault(dep_date, {})[carrier] = price
                except ValueError:
                    pass

    sorted_dates = sorted(daily_groups.keys())
    if not sorted_dates:
        return ElementaryIndexResponse(
            origin=target_orig,
            destination=target_dest,
            advance_window_days=advance_window_days,
            base_value=100.0,
            series_length=0,
            series=[],
        )

    # Convert to daily list of dicts for build_elementary_index
    daily_price_list = [daily_groups[d] for d in sorted_dates]
    elementary_values = build_elementary_index(daily_price_list, base_value=100.0)

    points = [
        ElementaryIndexPointOut(
            day=idx,
            index_value=round(val, 3),
            carrier_count=len(daily_price_list[idx]),
        )
        for idx, val in enumerate(elementary_values)
    ]

    return ElementaryIndexResponse(
        origin=target_orig,
        destination=target_dest,
        advance_window_days=advance_window_days,
        base_value=100.0,
        series_length=len(points),
        series=points,
    )


def get_source_status(data_dir: Optional[Path] = None) -> SourceStatusOut:
    """
    Summarize collection_method distribution and simulated fallback rate.
    Returns 200 with zero counts if fare_quote.csv is missing or empty.
    """
    directory = _resolve_data_dir(data_dir)
    csv_path = directory / "fare_quote.csv"

    if not csv_path.is_file():
        return SourceStatusOut(
            total_quotes=0,
            by_method={},
            fallback_simulated_percentage=0.0,
            status_note="No collection data available (fare_quote.csv absent).",
        )

    by_method: Dict[str, int] = {}
    total = 0

    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            method = row.get("collection_method", "unknown").strip().lower()
            by_method[method] = by_method.get(method, 0) + 1
            total += 1

    simulated_count = by_method.get("simulated", 0)
    simulated_pct = round((simulated_count / total * 100), 2) if total > 0 else 0.0

    return SourceStatusOut(
        total_quotes=total,
        by_method=by_method,
        fallback_simulated_percentage=simulated_pct,
        status_note=(
            "Aggregated from fare_quote.csv collection_method counts. "
            "Will transition to live resolver telemetry in future milestone."
        ),
    )


def get_quality_status(data_dir: Optional[Path] = None) -> QualityStatusOut:
    """
    Summarize data hygiene and quality flags.
    Returns 200 with zero counts if fare_quote.csv is missing or empty.
    """
    directory = _resolve_data_dir(data_dir)
    csv_path = directory / "fare_quote.csv"

    if not csv_path.is_file():
        return QualityStatusOut(
            total_quotes=0,
            by_quality_flag={},
            ok_count=0,
            sold_out_count=0,
            outlier_count=0,
            imputed_count=0,
        )

    by_flag: Dict[str, int] = {}
    total = 0

    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            flag = row.get("quality_flag", "ok").strip().lower()
            by_flag[flag] = by_flag.get(flag, 0) + 1
            total += 1

    return QualityStatusOut(
        total_quotes=total,
        by_quality_flag=by_flag,
        ok_count=by_flag.get("ok", 0),
        sold_out_count=by_flag.get("sold_out", 0),
        outlier_count=by_flag.get("outlier", 0),
        imputed_count=by_flag.get("imputed", 0),
    )

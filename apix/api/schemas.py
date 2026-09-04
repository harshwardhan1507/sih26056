"""
Pydantic V2 response schemas for the APIx FastAPI service.

Typed response contracts for all endpoints, plus a uniform ErrorResponse.

Every data-bearing response carries a ``DatasetProvenanceOut``. A consumer
must never have to guess whether the numbers it received were observed or
simulated -- the dashboard previously stamped ``dataset_type: "production"``
onto responses derived from a 100% simulated file.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

# Aliased because two models expose a field literally named `date`, which
# shadows the `date` type inside those class bodies and breaks annotation
# resolution under `from __future__ import annotations`.
DateField = date


class ErrorResponse(BaseModel):
    """Standardized error format returned across all API endpoints."""
    error: str = Field(..., description="Short machine-readable error code (e.g. 'data_unavailable')")
    detail: str = Field(..., description="Human-readable explanation of the error condition")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "error": "data_unavailable",
                "detail": "Required data file 'fare_quote.csv' is not available.",
            }
        }
    )


class DatasetProvenanceOut(BaseModel):
    """Where the served numbers came from, and how much of it is simulated."""
    dataset_type: str = Field(
        ...,
        description=(
            "'production' (no simulated rows), 'mixed' (some simulated), or "
            "'synthetic' (entirely simulated)"
        ),
    )
    source_file: str = Field(..., description="File the rows were read from")
    is_live_collection: bool = Field(
        ..., description="True if served from the live collection log, False if the demo artifact"
    )
    total_quotes: int = Field(..., description="Rows in the served dataset")
    observed_quotes: int = Field(..., description="Rows from api/tariff_sheet/scrape/historical_panel")
    simulated_quotes: int = Field(..., description="Rows produced by the simulator")
    simulated_percentage: float = Field(..., description="Percentage of rows that are simulated")
    note: str = Field(..., description="Human-readable provenance note")


class HealthResponse(BaseModel):
    """Liveness check and service status."""
    status: str = Field(default="ok", description="Service health status")
    version: str = Field(default="1.0.0", description="APIx version")
    timestamp_utc: datetime = Field(..., description="Current UTC timestamp of server")


class RouteItemOut(BaseModel):
    """A single route entry within the DGCA route basket."""
    route_id: str = Field(..., description="Canonical route identifier, e.g. 'DEL-BOM'")
    origin: str = Field(..., description="Origin 3-letter IATA code, e.g. 'DEL'")
    destination: str = Field(..., description="Destination 3-letter IATA code, e.g. 'BOM'")
    weight: float = Field(..., description="Laspeyres passenger traffic weight (sums to ~1.0)")


class RouteBasketOut(BaseModel):
    """Route basket with DGCA passenger traffic weights and source provenance."""
    source: str = Field(..., description="Data source description or 'placeholder' if falling back")
    coverage_month: Optional[str] = Field(None, description="DGCA reporting coverage period (YYYY-MM)")
    generated_date: Optional[str] = Field(None, description="Date weights were generated (YYYY-MM-DD)")
    total_basket_pax: Optional[int] = Field(None, description="Total passengers across basket routes")
    basket_share_of_domestic_pct: Optional[float] = Field(
        None, description="Share of all-India domestic traffic the basket covers"
    )
    routes: List[RouteItemOut] = Field(..., description="List of tracked routes and weights")


class QuoteOut(BaseModel):
    """Provenance-tagged airfare quote observation."""
    collected_at_utc: datetime = Field(..., description="UTC timestamp when the quote was recorded")
    observation_date: date = Field(
        ..., description="Day the fare was observed (departure minus the advance window)"
    )
    departure_date: date = Field(..., description="Flight departure date")
    advance_window_days: int = Field(..., description="Advance purchase lead window (1, 7, 15, 30, 45)")
    origin_iata: str = Field(..., description="Origin 3-letter IATA code")
    destination_iata: str = Field(..., description="Destination 3-letter IATA code")
    carrier_iata: str = Field(..., description="Operating carrier 2-letter IATA code")
    fare_class: str = Field(..., description="Travel class (Economy, Business, Premium)")
    total_fare_inr: Optional[float] = Field(None, description="Total consumer fare in INR (None if sold out)")
    source_id: str = Field(..., description="Identifier of adapter or source feed")
    collection_method: str = Field(
        ...,
        description="api | tariff_sheet | scrape | historical_panel | simulated | imputed",
    )
    quality_flag: str = Field(..., description="ok | outlier | imputed | sold_out")


class QuotesResponse(BaseModel):
    """Filtered list of collected fare quotes."""
    count: int = Field(..., description="Quotes returned in this response")
    total_matched: int = Field(..., description="Quotes matching the filters before any limit")
    provenance: DatasetProvenanceOut = Field(..., description="Where these quotes came from")
    quotes: List[QuoteOut] = Field(..., description="List of quote records")


class AggregateIndexPointOut(BaseModel):
    """A single daily point in the APIx aggregate index."""
    day: int = Field(..., description="Integer day index (0, 1, 2, ...)")
    date: Optional[DateField] = Field(None, description="Calendar date of this point")
    index_value: float = Field(..., description="Aggregate index value (Base = 100.0)")
    change_pct: Optional[float] = Field(None, description="Change versus the previous point")


class AggregateIndexResponse(BaseModel):
    """The headline aggregate index time series."""
    base_value: float = Field(default=100.0, description="Base index value at day 0")
    series_length: int = Field(..., description="Total points in the aggregate series")
    methodology: str = Field(
        ..., description="Aggregation method used, e.g. matched_jevons_fixed_base_laspeyres"
    )
    dataset_type: str = Field(..., description="'simulated' or 'production' per the series file")
    series: List[AggregateIndexPointOut] = Field(..., description="Daily index points")


class ElementaryIndexPointOut(BaseModel):
    """A single daily point in an elementary Jevons index series."""
    day: int = Field(..., description="Integer day index")
    date: DateField = Field(..., description="Observation date of this point")
    index_value: float = Field(..., description="Chained Jevons index relative to day 0")
    carrier_count: int = Field(..., description="Carriers priced on this day (0 = gap)")


class ElementaryIndexResponse(BaseModel):
    """Per-(route, advance_window) elementary Jevons index series."""
    origin: str = Field(..., description="Origin 3-letter IATA code")
    destination: str = Field(..., description="Destination 3-letter IATA code")
    advance_window_days: int = Field(..., description="Advance purchase lead window")
    base_value: float = Field(default=100.0, description="Base index value at day 0")
    series_length: int = Field(..., description="Total points in the elementary series")
    provenance: DatasetProvenanceOut = Field(..., description="Where the underlying quotes came from")
    series: List[ElementaryIndexPointOut] = Field(..., description="Daily elementary index points")


class RouteSummaryOut(BaseModel):
    """Computed headline figures for one route across all advance windows."""
    route_id: str
    origin: str
    destination: str
    weight: float
    current_index: Optional[float] = Field(None, description="Latest index level, None if no data")
    change_pct: Optional[float] = Field(None, description="Change versus the previous day")
    average_fare: Optional[float] = Field(None, description="Mean observed fare on the latest day")
    matched_observations: int = Field(..., description="Carrier-day observations behind this route")
    coverage_status: str = Field(..., description="complete | partial | insufficient")
    series_length: int = Field(..., description="Days in the underlying series")
    sparkline: List[float] = Field(..., description="Down-sampled index series for display")


class RouteSummaryResponse(BaseModel):
    """Per-route computed summaries."""
    count: int
    provenance: DatasetProvenanceOut
    routes: List[RouteSummaryOut]


class SourceStatusOut(BaseModel):
    """Collection breakdown by method and by source identifier."""
    total_quotes: int = Field(..., description="Total quotes recorded")
    by_method: Dict[str, int] = Field(..., description="Counts grouped by collection_method")
    by_source_id: Dict[str, int] = Field(
        ..., description="Counts grouped by the adapter that produced them"
    )
    fallback_simulated_percentage: float = Field(
        ..., description="Percentage of quotes relying on simulated fallback"
    )
    provenance: Optional[DatasetProvenanceOut] = Field(None, description="Served dataset provenance")
    status_note: str = Field(..., description="Diagnostic note regarding source telemetry")


class QualityStatusOut(BaseModel):
    """Data hygiene audit metrics."""
    total_quotes: int = Field(..., description="Total quotes analyzed")
    by_quality_flag: Dict[str, int] = Field(..., description="Counts grouped by quality_flag")
    ok_count: int = Field(..., description="Count of clean, valid quotes")
    sold_out_count: int = Field(..., description="Unavailable/sold-out quotes (missing prices)")
    outlier_count: int = Field(..., description="Quotes flagged as price outliers")
    imputed_count: int = Field(..., description="Quotes generated via imputation")
    quality_score: float = Field(..., description="Percentage of quotes flagged 'ok'")
    provenance: Optional[DatasetProvenanceOut] = Field(None, description="Served dataset provenance")

"""
Pydantic V2 response schemas for the APIx FastAPI service.

Defines typed response contracts for all 7 endpoints:
  - GET /health
  - GET /routes
  - GET /quotes
  - GET /index/elementary
  - GET /index/aggregate
  - GET /sources/status
  - GET /quality
And uniform ErrorResponse contract.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


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
    total_basket_pax: Optional[int] = Field(None, description="Total passenger count across basket routes")
    routes: List[RouteItemOut] = Field(..., description="List of tracked routes and weights")


class QuoteOut(BaseModel):
    """Provenance-tagged airfare quote observation."""
    collected_at_utc: datetime = Field(..., description="UTC timestamp when quote was scraped or recorded")
    departure_date: date = Field(..., description="Flight departure date")
    advance_window_days: int = Field(..., description="Advance purchase lead window (1, 7, 15, 30, 45)")
    origin_iata: str = Field(..., description="Origin 3-letter IATA code")
    destination_iata: str = Field(..., description="Destination 3-letter IATA code")
    carrier_iata: str = Field(..., description="Operating carrier 2-letter IATA code")
    fare_class: str = Field(..., description="Travel class (Economy, Business, Premium)")
    total_fare_inr: Optional[float] = Field(None, description="Total consumer fare in INR (None if sold out)")
    source_id: str = Field(..., description="Identifier of adapter or source feed")
    collection_method: str = Field(..., description="Method used: api | tariff_sheet | scrape | simulated | imputed")
    quality_flag: str = Field(..., description="Quality flag: ok | outlier | imputed | sold_out")


class QuotesResponse(BaseModel):
    """Paginated or filtered list of collected fare quotes."""
    count: int = Field(..., description="Number of quotes matching query filters")
    quotes: List[QuoteOut] = Field(..., description="List of quote records")


class AggregateIndexPointOut(BaseModel):
    """A single daily point in the APIx chained aggregate index."""
    day: int = Field(..., description="Integer day index (0, 1, 2, ...)")
    index_value: float = Field(..., description="Chained Laspeyres aggregate index value (Base = 100.0)")


class AggregateIndexResponse(BaseModel):
    """The chained Laspeyres aggregate index time series."""
    base_value: float = Field(default=100.0, description="Base index value at day 0")
    series_length: int = Field(..., description="Total points in the aggregate series")
    series: List[AggregateIndexPointOut] = Field(..., description="Daily index points")


class ElementaryIndexPointOut(BaseModel):
    """A single daily point in an elementary Jevons index series."""
    day: int = Field(..., description="Integer day index")
    index_value: float = Field(..., description="Chained Jevons elementary index relative to day 0")
    carrier_count: int = Field(..., description="Number of distinct carriers pricing on this day")


class ElementaryIndexResponse(BaseModel):
    """Per-(route, advance_window) elementary Jevons index series."""
    origin: str = Field(..., description="Origin 3-letter IATA code")
    destination: str = Field(..., description="Destination 3-letter IATA code")
    advance_window_days: int = Field(..., description="Advance purchase lead window")
    base_value: float = Field(default=100.0, description="Base index value at day 0")
    series_length: int = Field(..., description="Total points in the elementary series")
    series: List[ElementaryIndexPointOut] = Field(..., description="Daily elementary index points")


class SourceStatusOut(BaseModel):
    """Multi-tier collection breakdown and simulated fallback rate."""
    total_quotes: int = Field(..., description="Total quotes recorded")
    by_method: Dict[str, int] = Field(..., description="Counts grouped by collection_method")
    fallback_simulated_percentage: float = Field(..., description="Percentage of quotes relying on simulated fallback")
    status_note: str = Field(..., description="Diagnostic note regarding resolver and source telemetry")


class QualityStatusOut(BaseModel):
    """Data hygiene audit metrics: counts of ok, outlier, imputed, and sold_out."""
    total_quotes: int = Field(..., description="Total quotes analyzed")
    by_quality_flag: Dict[str, int] = Field(..., description="Counts grouped by quality_flag")
    ok_count: int = Field(..., description="Count of clean, valid quotes")
    sold_out_count: int = Field(..., description="Count of unavailable/sold-out quotes (missing prices)")
    outlier_count: int = Field(..., description="Count of quotes flagged as price outliers")
    imputed_count: int = Field(..., description="Count of quotes generated via imputation")

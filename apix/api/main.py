"""
FastAPI application for the APIx Airfare Price Index system.

Serves data to the frontend dashboard and external consumers (MoSPI / RBI):
  - GET /health           : Liveness and status check
  - GET /routes           : Route basket with DGCA passenger weights
  - GET /routes/summary   : Per-route computed index, fare and coverage
  - GET /quotes           : Filterable quote observations with provenance
  - GET /index/elementary : Per-(route, window) Jevons elementary series
  - GET /index/aggregate  : Fixed-base Laspeyres aggregate price index
  - GET /sources/status   : Multi-tier collection method telemetry & fallback rate
  - GET /quality          : Data hygiene audit metrics (ok, outlier, imputed, sold-out)
"""

from __future__ import annotations

import os
from datetime import date, datetime, timezone
from typing import Optional

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware

from . import data_access
from .errors import register_error_handlers
from .schemas import (
    AggregateIndexResponse,
    ElementaryIndexResponse,
    ErrorResponse,
    HealthResponse,
    QualityStatusOut,
    QuotesResponse,
    RouteBasketOut,
    RouteSummaryResponse,
    SourceStatusOut,
)

app = FastAPI(
    title="APIx Airfare Price Index API",
    description=(
        "Production-grade data delivery service for the APIx Airfare Price Index system "
        "(MoSPI CPI Problem Statement SIH-26056). Exposes route weights, price quotes, "
        "Jevons elementary series, fixed-base Laspeyres aggregates, and data-quality "
        "metrics. Every data response states whether its rows were observed or simulated."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    responses={
        503: {"model": ErrorResponse, "description": "Underlying data file unavailable"},
        400: {"model": ErrorResponse, "description": "Invalid parameter"},
        422: {"model": ErrorResponse, "description": "Validation error"},
    },
)

# Enable CORS for local and web dashboard integrations
# Read-only public data service. Origins are configurable via APIX_CORS_ORIGINS
# (comma-separated). Credentials are NOT allowed: the pairing of
# allow_origins=["*"] with allow_credentials=True is rejected by browsers and
# would be unsafe if it were not.
_cors_origins = [
    o.strip() for o in os.getenv(
        "APIX_CORS_ORIGINS",
        "http://localhost:3000,http://127.0.0.1:3000",
    ).split(",")
    if o.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)

# Register uniform ErrorResponse handlers
register_error_handlers(app)


@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Health"],
    summary="Liveness check",
    description="Returns current service health, API version, and server UTC timestamp.",
)
def get_health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version="1.0.0",
        timestamp_utc=datetime.now(timezone.utc),
    )


@app.get(
    "/routes",
    response_model=RouteBasketOut,
    tags=["Basket"],
    summary="Route basket & DGCA passenger weights",
    description=(
        "Returns the tracked Indian domestic route basket with passenger traffic weights "
        "and source attribution. Gracefully falls back to placeholder weights with "
        "'source': 'placeholder' if route_weights.json is absent."
    ),
)
def get_routes() -> RouteBasketOut:
    return data_access.get_routes()


@app.get(
    "/quotes",
    response_model=QuotesResponse,
    tags=["Quotes"],
    summary="Filterable fare quote records",
    description=(
        "Returns collected fare quotes from the served dataset (live collection "
        "log when present, otherwise the simulated demo artifact). Filters by "
        "origin, destination, advance window, and OBSERVATION date range; all "
        "active parameters are ANDed. Every response states its provenance."
    ),
)
def get_quotes(
    origin: Optional[str] = Query(None, description="Origin 3-letter IATA code, e.g. 'DEL'"),
    destination: Optional[str] = Query(None, description="Destination 3-letter IATA code, e.g. 'BOM'"),
    advance_window_days: Optional[int] = Query(None, description="Advance lead window (1, 7, 15, 30, 45)"),
    date_from: Optional[date] = Query(None, description="Filter observation date >= YYYY-MM-DD"),
    date_to: Optional[date] = Query(None, description="Filter observation date <= YYYY-MM-DD"),
    limit: Optional[int] = Query(None, ge=1, le=50000, description="Max quotes to return"),
) -> QuotesResponse:
    return data_access.get_quotes(
        origin=origin,
        destination=destination,
        advance_window_days=advance_window_days,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
    )


@app.get(
    "/index/elementary",
    response_model=ElementaryIndexResponse,
    tags=["Index"],
    summary="Elementary Jevons index series",
    description=(
        "Returns the chained Jevons elementary index for a specified route and advance window. "
        "Computes matched-sample geometric relatives across consecutive observation dates."
    ),
)
def get_elementary_index(
    origin: str = Query(..., description="Origin 3-letter IATA code, e.g. 'DEL'"),
    destination: str = Query(..., description="Destination 3-letter IATA code, e.g. 'BOM'"),
    advance_window_days: int = Query(..., description="Advance lead window, e.g. 7"),
    date_from: Optional[date] = Query(None, description="Filter observation date >= YYYY-MM-DD"),
    date_to: Optional[date] = Query(None, description="Filter observation date <= YYYY-MM-DD"),
) -> ElementaryIndexResponse:
    return data_access.get_elementary_index(
        origin=origin,
        destination=destination,
        advance_window_days=advance_window_days,
        date_from=date_from,
        date_to=date_to,
    )


@app.get(
    "/index/aggregate",
    response_model=AggregateIndexResponse,
    tags=["Index"],
    summary="Fixed-base Laspeyres aggregate index series",
    description=(
        "Returns the APIx aggregate index series. Base value is 100.0 at day 0. "
        "The response states the aggregation methodology and whether the "
        "underlying data is simulated."
    ),
)
def get_aggregate_index() -> AggregateIndexResponse:
    return data_access.get_aggregate_index()


@app.get(
    "/routes/summary",
    response_model=RouteSummaryResponse,
    tags=["Basket"],
    summary="Per-route computed index, fare and coverage",
    description=(
        "Computes each route's current index level, day-over-day change, latest "
        "average observed fare, matched observation count and a down-sampled "
        "sparkline from the served dataset. Routes with no observations return "
        "nulls and coverage_status='insufficient' rather than placeholder values."
    ),
)
def get_route_summary() -> RouteSummaryResponse:
    return data_access.get_route_summaries()


@app.get(
    "/sources/status",
    response_model=SourceStatusOut,
    tags=["Telemetry"],
    summary="Collection method breakdown & fallback rate",
    description=(
        "Surfaces the distribution of collection methods (api, tariff_sheet, scrape, simulated) "
        "and the simulated fallback percentage. Returns 200 with zero counts if no data exists."
    ),
)
def get_sources_status() -> SourceStatusOut:
    return data_access.get_source_status()


@app.get(
    "/quality",
    response_model=QualityStatusOut,
    tags=["Telemetry"],
    summary="Data quality and hygiene metrics",
    description=(
        "Returns counts of quotes by data-quality flag: ok, outlier, imputed, and sold_out. "
        "Returns 200 with zero counts if no data exists."
    ),
)
def get_quality() -> QualityStatusOut:
    return data_access.get_quality_status()

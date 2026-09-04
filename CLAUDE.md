# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

APIx (Airfare Price Index) is a real-time airfare index system for India designed for the Ministry of Statistics and Programme Implementation (MoSPI / NSO) to augment the Consumer Price Index (CPI 2024 series, Problem Statement SIH-26056).

The system automates daily price collection across 10–12 major Indian domestic routes (DGCA passenger-traffic weighted) across 5 advance-purchase windows (T+1, T+7, T+15, T+30, T+45) and computes chained index series using official national statistical methods.

## Environment & Commands

On this Windows environment, Python 3 is invoked using the Windows Python Launcher `py` (not bare `python` or `python3`):

```bash
# Run backfill simulation demo (outputs apix/data/fare_quote.csv and apix/data/index_series.csv)
py apix/backfill_demo.py

# Run daily 30-day back-test collection clock
py apix/collect_today.py
py apix/collect_today.py --date 2026-09-04

# Run all unit tests
py -m pytest tests/ -v

# Run individual test files directly with the launcher
py tests/test_index.py
py tests/test_derive_weights.py
py tests/test_kaggle_loader.py
py tests/test_resolver.py
py tests/test_cleaning.py
py tests/test_api.py

# Run FastAPI local server for dashboard and external consumers
py -m uvicorn apix.api.main:app --reload --port 8000

# Run a single test function with pytest
py -m pytest tests/test_index.py -k "test_jevons_ratio"

# Derive DGCA route weights from domestic city-pair traffic (aggregated/domestic/city.csv)
py scripts/derive_weights.py --help
py scripts/derive_weights.py --download

# Run arbitrary Python script
py path/to/script.py
```

## System Architecture

```
sih26056/
├── docs/
│   ├── SIH-26056-APIx-Team-Handbook.md   # Detailed handbook, methodology & research
│   ├── DAILY_COLLECTION_LOG.md           # Audit trail for 30-day collection clock
│   ├── KAGGLE_LOADER_REPORT.md           # Technical report on Kaggle historical panel loader
│   └── data-sources/
│       └── dgca-route-weights.md         # DGCA data source, ODbL-1.0 analysis & weights spec
├── scripts/
│   └── derive_weights.py                 # Reproducible DGCA route-weight derivation CLI
├── apix/
│   ├── collector/                        # Data ingestion layer
│   │   ├── adapters/
│   │   │   ├── base.py                   # FareQuote dataclass & FareSource abstract base class
│   │   │   ├── simulated.py              # Tier 4 simulator (advance decay, weekend surcharge)
│   │   │   └── kaggle.py                 # Tier 3 historical panel loader (EaseMyTrip 300k records)
│   │   ├── compliance/                   # Rate limiting, robots.txt, circuit breakers
│   │   └── resolver.py                   # FareResolver: carrier-aware multi-tier fallback
│   ├── cleaning/                         # Data hygiene (outlier detection, sold-out imputation)
│   ├── index/                            # Statistical index calculation
│   │   ├── elementary.py                 # Jevons elementary index (geometric mean of relatives, chained)
│   │   ├── aggregate.py                  # Chained Laspeyres aggregation with DGCA route weights
│   │   └── weights.py                    # External route-weight loader (from route_weights.json)
│   ├── api/                              # FastAPI service & OpenAPI endpoint
│   ├── data/                             # Generated & configured datasets
│   │   └── route_weights.json            # DGCA-derived 12-route weights (T12M 2025-06 to 2026-05)
│   ├── backfill_demo.py                  # 45-day offline index backfill simulation
│   └── collect_today.py                  # Daily live collection driver
└── tests/
    ├── fixtures/
    │   └── sample_clean_dataset.csv      # Test fixture for Kaggle loader tests
    ├── test_index.py                     # Unit tests for Jevons, Laspeyres, and weight validation
    ├── test_derive_weights.py            # Unit tests for DGCA weight derivation
    ├── test_kaggle_loader.py             # Unit tests for Kaggle panel parsing and window mapping
    └── test_resolver.py                  # Unit tests for FareResolver priority and fallback
```

### Key Components & Data Flow

1. **Collector & Adapter Contract (`apix/collector/adapters/`)**
   - Every source implements `FareSource.get_quotes(origin, destination, as_of_date, advance_window_days, carriers) -> list[FareQuote]`.
   - Every `FareQuote` tracks strict provenance: `source_id`, `collection_method` (`api`, `tariff_sheet`, `scrape`, `simulated`, `imputed`), and `quality_flag` (`ok`, `outlier`, `sold_out`, `imputed`).
   - `apix/collector/resolver.py` orchestrates multi-tier fallback (Tier 1 API $\to$ Tier 2 Tariff Sheet $\to$ Tier 3 Scrape $\to$ Tier 4 Simulated). Fallback is **carrier-aware**: if an adapter returns fares for some carriers but not others, lower tiers are queried only for the missing carriers and results are merged.

2. **Index Methodology (`apix/index/`)**
   - **Elementary Level (`elementary.py`)**: Uses the **Jevons index** (geometric mean of price relatives) rather than Carli or Dutot arithmetic means to handle high intraday airline price dispersion. Implements matched-sample chaining: only carriers present on both today and yesterday enter the ratio.
   - **Upper-Level Aggregation (`aggregate.py`)**: Combines elementary indices into the aggregate APIx series using a **chained Laspeyres** formula weighted by route traffic shares.
   - **Configurable Weights (`weights.py` & `scripts/derive_weights.py`)**: Route weights are decoupled from code into `apix/data/route_weights.json` so MoSPI PSD weights can replace defaults at runtime.

3. **Multi-Airport Resolution Policy**
   - **Goa:** Both Dabolim (`GOI`) and Manohar International Airport at Mopa (`GOX`, opened Jan 2023) serve the Goa metropolitan market. Route weights use **Metropolitan Catchment Aggregation** (summing `GOI` + `GOX` traffic) to reflect true consumer expenditure.
   - **Mumbai:** Both CSMT (`BOM`) and Navi Mumbai (`NMI`) normalize to the metropolitan code `BOM`.

## Airfare Index Rules & Domain Constraints

- **Never cross advance-purchase windows**: Compare T+7 today vs T+7 yesterday. Comparing different windows (e.g. T+7 vs T+30) represents a quality difference, not a pure price change.
- **Sold-out flights are missing, not zero**: If a flight is unavailable, `total_fare_inr` must be `None` with `quality_flag="sold_out"`. Never use `0.00`. In matched-sample chaining, sold-out flights drop out of that day's pair.
- **Consumer price scope**: Uses total fare paid by consumer including mandatory fees and OTA convenience fee (following BLS CPI standard for consumer price indices).
- **Data transparency**: Any simulated records must always maintain `collection_method="simulated"`.

## Git & Collaboration Rules

- Do **not** add Claude as a collaborator or co-author. Never add `Co-Authored-By: Claude Code` to git commit messages or git configs.

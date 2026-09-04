# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

APIx (Airfare Price Index) is a real-time airfare index system for India designed for the Ministry of Statistics and Programme Implementation (MoSPI / NSO) to augment the Consumer Price Index (CPI 2024 series, Problem Statement SIH-26056).

The system automates daily price collection across 12 major Indian domestic routes (DGCA passenger-traffic weighted) across 5 advance-purchase windows (T+1, T+7, T+15, T+30, T+45) and computes index series using official national statistical methods.

## Environment & Commands

On this Windows environment, Python 3 is invoked using the Windows Python Launcher `py` (not bare `python` or `python3`):

```bash
# Run backfill simulation demo (outputs apix/data/fare_quote.csv and apix/data/index_series.csv)
py apix/backfill_demo.py

# Run daily 30-day back-test collection clock
py apix/collect_today.py
py apix/collect_today.py --date 2026-09-04
py apix/collect_today.py --date 2026-09-04 --force   # re-collect, replacing that day

# Advance the collection clock and update the audit log
py scripts/run_daily_collection.py

# Run all unit tests
py -m pytest tests/ -v

# Run individual test files directly with the launcher
py tests/test_index.py
py tests/test_derive_weights.py
py tests/test_kaggle_loader.py
py tests/test_resolver.py
py tests/test_cleaning.py
py tests/test_api.py
py tests/test_tariff_sheet.py
py tests/test_tariff_carriers.py
py tests/test_har_replay_scraper.py
py tests/test_kaggle_backtest.py

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
├── LICENSE                               # MIT + third-party data notices (ODbL-1.0)
├── docs/
│   ├── SIH-26056-APIx-Team-Handbook.md   # Handbook, methodology & research
│   ├── METHODOLOGY_CHAIN_DRIFT.md        # NORMATIVE: aggregation method & assumptions
│   ├── DAILY_COLLECTION_LOG.md           # Audit trail for the collection clock
│   ├── KAGGLE_50DAY_BACKTEST_REPORT.md   # Generated back-test report
│   ├── KAGGLE_LOADER_REPORT.md           # Historical panel loader notes
│   └── data-sources/                     # Source dossiers & licence analysis
├── scripts/
│   ├── derive_weights.py                 # DGCA route-weight derivation CLI
│   ├── run_daily_collection.py           # Collection clock driver (idempotent)
│   ├── run_kaggle_backtest.py            # 50-day historical back-test
│   └── schedule_daily_collection.ps1     # Windows Task Scheduler registration
├── apix/
│   ├── collector/
│   │   ├── adapters/
│   │   │   ├── base.py                   # FareQuote + FareSource contract
│   │   │   ├── simulated.py              # Tier 4 simulator
│   │   │   ├── tariff_sheet.py           # Tier 2 IndiGo + shared band logic
│   │   │   ├── tariff_carriers.py        # Tier 2 Air India, Akasa
│   │   │   ├── har_replay_scraper.py     # Tier 3 HAR replay (NO live scraping)
│   │   │   ├── kaggle.py                 # Historical EaseMyTrip panel loader
│   │   │   └── fixtures/                 # Committed tariff sheet extracts
│   │   ├── compliance/
│   │   │   ├── rate_limiter.py           # Per-host polite rate limiting
│   │   │   ├── robots.py                 # robots.txt gate (fail-closed)
│   │   │   ├── off_peak.py               # IST 02:00-05:00 window
│   │   │   └── circuit_breaker.py        # Trips out failing sources
│   │   └── resolver.py                   # Carrier-aware multi-tier resolution
│   ├── cleaning/                         # schema, dedup, outliers, imputation, pipeline
│   ├── index/
│   │   ├── elementary.py                 # Matched-sample chained Jevons
│   │   ├── aggregate.py                  # Fixed-base Laspeyres (+ diagnostics)
│   │   └── weights.py                    # External weight-file loader
│   ├── api/                              # FastAPI service (8 endpoints)
│   ├── data/                             # Generated artifacts + route_weights.json
│   ├── backfill_demo.py                  # 45-day simulated backfill
│   └── collect_today.py                  # One-day collection snapshot
├── apix-dashboard/                       # Next.js 16 dashboard
└── tests/                                # 114 tests
```

### Key Components & Data Flow

1. **Collector & Adapter Contract (`apix/collector/adapters/`)**
   - Every source implements `FareSource.get_quotes(origin, destination, as_of_date, advance_window_days, carriers) -> list[FareQuote]`.
   - Every `FareQuote` tracks strict provenance: `source_id`, `collection_method` (`api`, `tariff_sheet`, `scrape`, `simulated`, `imputed`), and `quality_flag` (`ok`, `outlier`, `sold_out`, `imputed`).
   - `apix/collector/resolver.py` orchestrates multi-tier fallback (Tier 1 API $\to$ Tier 2 Tariff Sheet $\to$ Tier 3 Scrape $\to$ Tier 4 Simulated). Fallback is **carrier-aware**: if an adapter returns fares for some carriers but not others, lower tiers are queried only for the missing carriers and results are merged.

2. **Index Methodology (`apix/index/`)** — see `docs/METHODOLOGY_CHAIN_DRIFT.md` (normative)
   - **Elementary Level (`elementary.py`)**: **Jevons index** (geometric mean of price relatives) rather than Carli or Dutot arithmetic means, to handle high intraday airline price dispersion. Matched-sample chaining: only carriers priced on both the current and reference day enter the ratio. Gaps are bridged against the last day with prices, so a missed collection day does not permanently erase real movement.
   - **Upper-Level Aggregation (`aggregate.py`)**: **Fixed-base Laspeyres**, NOT daily-chained. A daily chain of weighted arithmetic relatives is upward-biased by `exp(sigma^2)` per link and manufactures inflation from noise. `method="chained"` is retained for drift diagnostics only and must never be published.
   - **Configurable Weights (`weights.py` & `scripts/derive_weights.py`)**: Route weights are decoupled from code into `apix/data/route_weights.json` so MoSPI PSD weights can replace defaults at runtime. The derivation CLI auto-detects the latest trailing-12-month window.

4. **Cleaning (`apix/cleaning/`)** — wired into every collection run via `collect_today.py`. Schema validation, precedence-based deduplication, **time-relative** outlier screening (per carrier against its own history, never cross-sectionally against competitors), and optional CPI class-mean imputation.

5. **API (`apix/api/`)** — serves the live collection log when present, else the simulated demo. Every data response carries a `provenance` block stating `dataset_type` (`production` / `mixed` / `synthetic`) and the simulated share.

3. **Multi-Airport Resolution Policy**
   - **Goa:** Both Dabolim (`GOI`) and Manohar International Airport at Mopa (`GOX`, opened Jan 2023) serve the Goa metropolitan market. Route weights use **Metropolitan Catchment Aggregation** (summing `GOI` + `GOX` traffic) to reflect true consumer expenditure.
   - **Mumbai:** Both CSMT (`BOM`) and Navi Mumbai (`NMI`) normalize to the metropolitan code `BOM`.

## Airfare Index Rules & Domain Constraints

- **Never cross advance-purchase windows**: Compare T+7 today vs T+7 yesterday. Comparing different windows (e.g. T+7 vs T+30) represents a quality difference, not a pure price change.
- **Sold-out flights are missing, not zero**: If a flight is unavailable, `total_fare_inr` must be `None` with `quality_flag="sold_out"`. Never use `0.00`. In matched-sample chaining, sold-out flights drop out of that day's pair.
- **Consumer price scope**: Uses total fare paid by consumer including mandatory fees and OTA convenience fee (following BLS CPI standard for consumer price indices).
- **Data transparency**: Simulated records must always carry `collection_method="simulated"`. More broadly: **never label generated data as observed.** No hardcoded metric may be presented as measured — if a value is unknown, return `None`/`null` and let the UI render a dash. This applies to API responses, dashboard providers, generated reports and committed CSV artifacts alike.
- **Never cross the observation/departure axis**: the index's time axis is the OBSERVATION date (`departure_date - advance_window_days`), exposed as `FareQuote.observation_date`. Grouping on `departure_date` only works within a single window and misaligns the moment two windows share a calendar.
- **Collection is idempotent**: re-running a date replaces it. The audit log in `docs/DAILY_COLLECTION_LOG.md` must always agree with `fare_quote_log.csv`; a row there that the CSV does not back is an audit defect.
- **Fail loudly, not silently**: a missing dependency, an unreachable source or a contract violation must raise or log, never quietly degrade to the simulator with no signal.

## Git & Collaboration Rules

- Do **not** add Claude as a collaborator or co-author. Never add `Co-Authored-By: Claude Code` to git commit messages or git configs.

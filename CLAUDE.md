# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

APIx (Airfare Price Index) is a real-time airfare index system for India designed for the Ministry of Statistics and Programme Implementation (MoSPI / NSO) to augment the Consumer Price Index (CPI 2024 series, Problem Statement SIH-26056).

The system automates daily price collection across 10–12 major Indian domestic routes (DGCA passenger-traffic weighted) across 5 advance-purchase windows (T+1, T+7, T+15, T+30, T+45) and computes chained index series using official national statistical methods.

## Environment & Commands

On this Windows environment, Python 3 is invoked using the Windows Python Launcher `py` (not bare `python` or `python3`):

```bash
# Run backfill simulation demo (outputs data/fare_quote.csv and data/index_series.csv)
py apix/backfill_demo.py
# Or inside package directory:
cd apix && py backfill_demo.py

# Run tests
py tests/test_index.py
py tests/test_derive_weights.py
py tests/test_kaggle_loader.py
py tests/test_resolver.py
# Or with pytest once installed:
py -m pytest tests/ -v

# Derive DGCA route weights from domestic city-pair traffic
py scripts/derive_weights.py --help
py scripts/derive_weights.py --download

# Run Python module or script
py path/to/script.py
```

## System Architecture

```
sih26056/
├── docs/
│   └── SIH-26056-APIx-Team-Handbook.md  # Detailed handbook, methodology & research
├── apix/
│   ├── collector/          # Data ingestion layer
│   │   ├── adapters/
│   │   │   ├── base.py     # FareQuote dataclass & FareSource abstract base class
│   │   │   └── simulated.py# Tier 4 simulator (advance decay, weekend surcharge, carrier spread)
│   │   ├── compliance/     # Rate limiting, robots.txt, circuit breakers
│   │   └── resolver.py     # Priority fallback: Tier 1 (API) -> Tier 2 (Tariff Sheet) -> Tier 3 (Scrape) -> Tier 4 (Simulated)
│   ├── cleaning/           # Data hygiene (outlier detection, sold-out imputation)
│   ├── index/              # Statistical index calculation
│   │   ├── elementary.py   # Jevons elementary index (geometric mean of relatives, chained, matched-sample)
│   │   └── aggregate.py    # Chained Laspeyres aggregation with DGCA route weights
│   ├── api/                # FastAPI service & OpenAPI endpoint
│   └── data/               # Generated datasets (fare_quote.csv, index_series.csv)
└── tests/
    └── test_index.py       # Unit tests for Jevons and Laspeyres formulas
```

### Key Components

1. **Collector & Adapter Contract (`apix/collector/adapters/base.py`)**
   - Every source implements `FareSource.get_quotes(origin, destination, as_of_date, advance_window_days, carriers) -> list[FareQuote]`.
   - Every `FareQuote` tracks strict provenance: `source_id`, `collection_method` (`api`, `tariff_sheet`, `scrape`, `simulated`, `imputed`), and `quality_flag` (`ok`, `outlier`, `sold_out`, `imputed`).
   - `resolver.py` orchestrates multi-tier fallback without modifying index or downstream consumers.

2. **Index Methodology (`apix/index/`)**
   - **Elementary Level (`elementary.py`)**: Uses the **Jevons index** (geometric mean of price relatives) rather than Carli or Dutot arithmetic means to handle high intraday airline price dispersion. Implements matched-sample chaining: only carriers present on both today and yesterday enter the ratio.
   - **Upper-Level Aggregation (`aggregate.py`)**: Combines elementary indices into the aggregate APIx series using a **chained Laspeyres** formula weighted by route traffic shares.
   - Route basket and weights are designed to be configurable via external files for MoSPI PSD (Price Statistics Division) alignment.

## Airfare Index Rules & Domain Constraints

- **Never cross advance-purchase windows**: Compare T+7 today vs T+7 yesterday. Comparing different windows (e.g. T+7 vs T+30) represents a quality difference, not a pure price change.
- **Sold-out flights are missing, not zero**: If a flight is unavailable, `total_fare_inr` must be `None` with `quality_flag="sold_out"`. Never use `0.00`. In matched-sample chaining, sold-out flights drop out of that day's pair.
- **Consumer price scope**: Uses total fare paid by consumer including mandatory fees and OTA convenience fee (following BLS CPI standard for consumer price indices).
- **Data transparency**: Any simulated records must always maintain `collection_method="simulated"`.

## Git & Collaboration Rules

- Do **not** add Claude as a collaborator or co-author. Never add `Co-Authored-By: Claude Code` to git commit messages or git configs.

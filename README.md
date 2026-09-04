# APIx — Real-time Airfare Price Index for India

[![Smart India Hackathon 2026](https://img.shields.io/badge/SIH-2026-blue.svg)](https://www.sih.gov.in/)
[![Problem Statement](https://img.shields.io/badge/MoSPI-PS--26056-green.svg)](docs/SIH-26056-APIx-Team-Handbook.md)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](LICENSE)

> **Augmenting the Consumer Price Index (CPI 2024 Series)** through automated daily price collection, multi-tier source resolution, and international statistical index methodology.

---

## Executive Summary

Under the revised CPI series (2024=100) launched in February 2026, the **Ministry
of Statistics and Programme Implementation (MoSPI / NSO)** moved airfare price
collection online via State Regional Offices, on a weekly basis.

**APIx industrialises that process:**

- **Frequency** — daily automated collection instead of weekly manual.
- **Market windows** — 5 advance-purchase horizons (T+1, T+7, T+15, T+30, T+45),
  never compared across windows.
- **Representative basket** — 12 trunk routes weighted by DGCA passenger traffic.
- **Statistical method** — matched-sample **Jevons** at the elementary level,
  **fixed-base Laspeyres** at the upper level (see the note below).
- **Provenance** — every quote carries `source_id`, `collection_method` and
  `quality_flag`; every API response states whether its rows were observed or
  simulated.

### A note on aggregation

APIx does **not** daily-chain its aggregate index. A daily chain of weighted
arithmetic price relatives is upward-biased by `exp(σ²)` per link, which
compounds noise into inflation that is not there — for airfare-scale dispersion,
roughly **+0.64% per day of spurious movement**. The index therefore uses a
fixed-base Laspeyres, re-linkable at long intervals.

This is not a stylistic preference; it is the reason CPI itself is not
daily-chained. Full derivation, empirical verification and citations:
**[docs/METHODOLOGY_CHAIN_DRIFT.md](docs/METHODOLOGY_CHAIN_DRIFT.md)**.

---

## Repository Structure

```
sih26056/
├── LICENSE                          # MIT + third-party data notices (ODbL-1.0 etc.)
├── CLAUDE.md                        # Contributor & code-style guide
├── requirements.txt                 # Python dependencies
│
├── docs/
│   ├── SIH-26056-APIx-Team-Handbook.md    # Problem statement & team handbook
│   ├── METHODOLOGY_CHAIN_DRIFT.md         # Aggregation methodology (normative)
│   ├── DAILY_COLLECTION_LOG.md            # Collection clock audit trail
│   ├── KAGGLE_50DAY_BACKTEST_REPORT.md    # Back-test report (generated)
│   ├── KAGGLE_LOADER_REPORT.md            # Historical panel loader notes
│   ├── api.md                             # API reference
│   └── data-sources/
│       ├── dgca-route-weights.md          # DGCA weights: source & ODbL analysis
│       ├── TARIFF_SHEET_SOURCES.md        # Rule 135(2) tariff sheet sources
│       ├── MOSPI_CPI2024_AIRFARE.md       # CPI 2024 methodology research
│       └── COMMERCIAL_API_OUTREACH.md     # Tier 1 API access register
│
├── scripts/
│   ├── derive_weights.py            # DGCA route-weight derivation CLI
│   ├── run_daily_collection.py      # Daily collection clock driver
│   ├── run_kaggle_backtest.py       # 50-day historical back-test
│   └── schedule_daily_collection.ps1 # Windows Task Scheduler registration
│
├── apix/
│   ├── collector/
│   │   ├── adapters/
│   │   │   ├── base.py              # FareQuote + FareSource contract
│   │   │   ├── simulated.py         # Tier 4 simulator
│   │   │   ├── tariff_sheet.py      # Tier 2 — IndiGo, shared band logic
│   │   │   ├── tariff_carriers.py   # Tier 2 — Air India, Akasa
│   │   │   ├── har_replay_scraper.py # Tier 3 — HAR replay (no live scraping)
│   │   │   ├── kaggle.py            # Historical EaseMyTrip panel loader
│   │   │   └── fixtures/            # Committed tariff sheet extracts
│   │   ├── compliance/
│   │   │   ├── rate_limiter.py      # Per-host polite rate limiting
│   │   │   ├── robots.py            # robots.txt gate (fail-closed)
│   │   │   ├── off_peak.py          # IST 02:00–05:00 collection window
│   │   │   └── circuit_breaker.py   # Trips out repeatedly failing sources
│   │   └── resolver.py              # Multi-tier, carrier-aware resolution
│   ├── cleaning/
│   │   ├── schema.py                # Validation & coercion
│   │   ├── deduplication.py         # Precedence-based dedup
│   │   ├── outliers.py              # Time-relative outlier screening
│   │   ├── imputation.py            # CPI class-mean imputation
│   │   └── pipeline.py              # Orchestration + audit report
│   ├── index/
│   │   ├── elementary.py            # Matched-sample chained Jevons
│   │   ├── aggregate.py             # Fixed-base Laspeyres (+ diagnostics)
│   │   └── weights.py               # External weight-file loader
│   ├── api/                         # FastAPI service (8 endpoints)
│   ├── data/                        # Generated artifacts + route weights
│   ├── backfill_demo.py             # 45-day simulated backfill
│   └── collect_today.py             # One-day collection snapshot
│
├── apix-dashboard/                  # Next.js 16 dashboard
│   ├── app/                         # Routes: overview, trend, routes, sources, quality
│   ├── components/                  # Charts, tables, layout
│   └── lib/api/                     # Fixture + live FastAPI providers
│
└── tests/                           # 114 tests
```

---

## Quickstart

### 1. Setup

Python 3.11+. On Windows, `py` and `python` both work.

```bash
git clone https://github.com/harshwardhan1507/sih26056.git
cd sih26056
pip install -r requirements.txt
```

### 2. Generate the simulated backfill

45 days × 12 routes × 5 windows through the full pipeline:

```bash
py apix/backfill_demo.py
```

Writes `apix/data/fare_quote.csv` (13,500 provenance-tagged quotes, every row
labelled `dataset_type=simulated`) and `apix/data/index_series.csv`. The run
prints both the headline fixed-base index and the daily-chained figure, so the
drift the method avoids stays visible.

### 3. Run a real collection

```bash
py scripts/run_daily_collection.py
```

Resolves through Tier 2 tariff sheets (IndiGo, Air India, Akasa) with simulated
fallback for carriers that publish no sheet, cleans the result, and writes one
**idempotent** day to `data/raw/live_collection/fare_quote_log.csv`. Re-running
a date replaces it rather than duplicating it. Register it daily with
`scripts/schedule_daily_collection.ps1`.

### 4. Serve the API

```bash
py -m uvicorn apix.api.main:app --reload --port 8000
```

Docs at http://localhost:8000/docs. The API serves the live collection log when
one exists and falls back to the simulated demo otherwise — and says which, in
every response's `provenance` block.

### 5. Run the dashboard

```bash
cd apix-dashboard && npm install && npm run dev
```

Set `NEXT_PUBLIC_API_BASE_URL=http://localhost:8000` in `.env.local` for live
mode; without it the dashboard runs on fixtures and labels itself Local Demo.

### 6. Run the tests

```bash
py -m pytest tests/ -v
```

---

## Methodological Highlights

1. **Jevons elementary index** — geometric mean of price relatives over carriers
   matched on both days:

   $$I^{t/t-1}_{\text{Jevons}} = \prod_{i \in S_{t,t-1}} \left(\frac{P_{i,t}}{P_{i,t-1}}\right)^{1/n}$$

   Prevents the arithmetic skew that dynamic airline pricing induces. Gaps are
   bridged against the last day that had prices, so a missed collection day does
   not permanently erase real price movement from the chain.

2. **Fixed-base Laspeyres upper level** — drift-free by construction. If prices
   rise and return to their starting level, the index returns to exactly 100
   (verified in `tests/test_index.py`).

3. **Sold out is missing, not zero** — unavailable flights carry
   `total_fare_inr = None` with `quality_flag="sold_out"` and drop out of that
   day's matched sample. Never recorded as ₹0.

4. **Outliers screened on time relatives** — each carrier against its own price
   history, not against its competitors. A full-service carrier costing more
   than an LCC is a real price, not a data error.

5. **Consumer price scope** — the target concept is the total fare a consumer
   pays, including mandatory fees and OTA convenience charges (BLS CPI
   convention). Note the current Tier 2 caveat: DGCA tariff sheets publish
   **base fare excluding taxes**, so tariff-sourced quotes understate the
   consumer price. Tracked in
   [docs/METHODOLOGY_CHAIN_DRIFT.md](docs/METHODOLOGY_CHAIN_DRIFT.md) §9.

---

## Data Provenance

Every artifact states what it is. Nothing in this repository presents generated
data as observed data.

| Source tier | Status | `collection_method` |
|---|---|---|
| Tier 1 — commercial APIs (TripJack, TBO) | **Not integrated.** Access requests pending; no adapter exists. | — |
| Tier 2 — DGCA Rule 135(2) tariff sheets | Live for IndiGo, Air India, Akasa | `tariff_sheet` |
| Tier 3 — OTA collection | HAR replay only; **no live scraper** | `scrape` |
| Historical — EaseMyTrip panel | Loader implemented; dataset not redistributed | `historical_panel` |
| Tier 4 — simulator | Fallback for carriers no tier reaches | `simulated` |

The back-test script generates a synthetic stand-in panel when the real Kaggle
dataset is absent. When it does, every row it writes is labelled
`sample_type=synthetic_stand_in` and the report leads with a warning banner.

---

## License

MIT for the software — see [LICENSE](LICENSE). Third-party data carries its own
terms: DGCA route weights are **ODbL-1.0** (share-alike; attribution required),
and the EaseMyTrip panel is subject to Kaggle's terms. Both are detailed in the
LICENSE file's third-party data notice.

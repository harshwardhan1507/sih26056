# APIx — Real-time Airfare Price Index for India

[![Smart India Hackathon 2026](https://img.shields.io/badge/SIH-2026-blue.svg)](https://www.sih.gov.in/)
[![Problem Statement](https://img.shields.io/badge/MoSPI-PS--26056-green.svg)](docs/SIH-26056-APIx-Team-Handbook.md)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](LICENSE)

> **Augmenting the Consumer Price Index (CPI 2024 Series)** through automated daily price collection, multi-tier source resolution, and rigorous international statistical index methodology.

---

## 📌 Executive Summary

Under the revised CPI series (2024=100) launched in February 2026, the **Ministry of Statistics and Programme Implementation (MoSPI / NSO)** transitioned airfare price collection online via State Regional Offices on a weekly basis.

**APIx industrializes this process**:
- **Frequency**: Shifts collection from weekly-manual to **daily-automated**.
- **Market Windows**: Tracks 5 advance-purchase horizons (**T+1, T+7, T+15, T+30, T+45**) — never comparing across windows to avoid quality-mix distortion.
- **Representative Basket**: Weighted dynamically by **DGCA passenger-traffic volume** across top Indian domestic city pairs.
- **Statistical Rigor**: Implements **Jevons geometric mean** at the elementary level (invariant to extreme intraday airline price swings) and **chained Laspeyres** upper-level aggregation.
- **Data Provenance**: Every quote is tagged with `source_id`, `collection_method`, and `quality_flag`.

For the complete technical blueprint and pitch strategy, consult the [Team Handbook & Resource Pack](docs/SIH-26056-APIx-Team-Handbook.md).

---

## 📁 Repository Structure

```
sih26056/
├── .gitignore                      # Python bytecode, environments, and cache exclusions
├── CLAUDE.md                       # AI developer and code style guide
├── README.md                       # Main repository documentation (this file)
├── requirements.txt                # Python dependencies
│
├── docs/
│   └── SIH-26056-APIx-Team-Handbook.md  # Comprehensive problem statement & team handbook
│
├── apix/                           # Core APIx Python package
│   ├── __init__.py
│   ├── README.md                   # Scaffold documentation
│   ├── backfill_demo.py            # 45-day offline simulation runner
│   │
│   ├── collector/                  # Data ingestion layer
│   │   ├── __init__.py
│   │   ├── adapters/
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # FareSource abstract interface & FareQuote dataclass
│   │   │   └── simulated.py        # Tier 4 simulator with advance decay & sold-out logic
│   │   └── compliance/             # Rate limiting, robots.txt, circuit breakers
│   │       └── __init__.py
│   │
│   ├── cleaning/                   # Data hygiene (outlier detection & imputation)
│   │   └── __init__.py
│   │
│   ├── index/                      # Statistical index computation
│   │   ├── __init__.py
│   │   ├── elementary.py           # Jevons elementary index (matched-sample chained)
│   │   └── aggregate.py            # Chained Laspeyres upper-level aggregation
│   │
│   ├── api/                        # FastAPI / OpenAPI delivery endpoints
│   │   └── __init__.py
│   │
│   └── data/                       # Generated dataset artifacts
│       ├── fare_quote.csv          # Granular quote-level log with provenance
│       └── index_series.csv        # Aggregated daily index series
│
└── tests/                          # Automated testing suite
    ├── __init__.py
    └── test_index.py               # Unit tests verifying index mathematical formulas
```

---

## 🚀 Quickstart

### 1. Requirements & Setup
Ensure you have Python 3.11+ installed. (On Windows, you can run using `py`).

```bash
# Clone the repository
git clone https://github.com/harshwardhan1507/sih26056.git
cd sih26056

# Optional: Install dependencies
pip install -r requirements.txt
```

### 2. Run the 45-Day Backfill Simulation
Runs 45 days × 12 routes × 5 advance-purchase windows through the full pipeline:

```bash
py apix/backfill_demo.py
# Or inside the package directory:
cd apix && py backfill_demo.py
```

This generates:
- `apix/data/fare_quote.csv`: 13,500 simulated quotes with full provenance and quality tags.
- `apix/data/index_series.csv`: Daily APIx aggregate index series.

### 3. Run Automated Tests
Validate the statistical formulas (Jevons geometric mean, matched-sample handling, and Laspeyres upper-level chaining):

```bash
py tests/test_index.py
# or using pytest
py -m pytest tests/ -v
```

---

## 📐 Methodological Highlights

1. **Jevons Elementary Index**:
   $$I_{\text{Jevons}}^{t / t-1} = \prod_{i \in S_{t, t-1}} \left(\frac{P_{i, t}}{P_{i, t-1}}\right)^{\frac{1}{n}}$$
   Uses geometric mean over matched carriers $S_{t, t-1}$ to prevent arithmetic skew from dynamic pricing volatility.
2. **Missing Price Handling**: Sold-out flights are treated as missing data (`quality_flag="sold_out"`), not zero prices, and drop out cleanly from matched-sample comparisons.
3. **Consumer Price Inclusivity**: All taxes, mandatory fees, and OTA convenience fees are included in the price relative, reflecting true consumer expenditure (aligned with BLS CPI standards).

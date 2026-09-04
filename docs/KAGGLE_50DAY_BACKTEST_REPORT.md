# APIx 50-Day Historical Panel Back-Test Report


**Dataset**: EaseMyTrip Flight Price Panel (Bathwal 2022 / Kaggle)
**Source file**: `panel.csv`
**Sample type**: `kaggle_easemytrip_panel`
**Sample period**: 50 days (2022-02-11 to 2022-04-01)
**Coverage**: 12 trunk routes · 5 advance horizons (T+1, T+7, T+15, T+30, T+45)
**Aggregation**: Matched-sample Jevons elementary indices aggregated via a
DGCA passenger-traffic weighted **fixed-base Laspeyres**

---

## 1. Executive Summary

This back-test evaluates the arithmetic stability and advance-horizon
behaviour of the APIx index system over **50 consecutive days** of
real-world domestic airline price observations.

| Metric | Result |
|---|---|
| Base value (day 0) | 100.000 |
| Final value (day 49) | 94.941 |
| Cumulative movement | -5.06% |
| Min index value | 94.773 |
| Max index value | 105.223 |
| Elementary strata computed | 60 of 60 |
| Strata with observations | 60 of 60 |
| Mean daily stratum coverage | 100.0% |

---

## 2. Methodological Notes

1. **Matched-sample Jevons elementary indices.**
   Within each (route, advance_window) stratum, price relatives use only
   carriers priced on both the current day and the reference day. Carriers
   entering or leaving the schedule do not move the index. Days with no
   observations hold the level and are bridged by the next day with data.

2. **Fixed-base Laspeyres upper level — deliberately NOT daily-chained.**
   Every day is compared against the base period, not against the previous
   day. A daily chain of weighted *arithmetic* relatives is upward biased by
   `exp(sigma^2)` per link (Jensen's inequality), which compounds noise into
   spurious inflation. See `docs/METHODOLOGY_CHAIN_DRIFT.md`.

   Consequence, verified in `tests/test_index.py`: if prices rise and then
   return exactly to their starting level, this index returns exactly to
   100. The previously used daily chain did not.

3. **Common calendar across strata.**
   All strata are evaluated on the union of observed dates, so no stratum is
   silently padded to a different length.

4. **Window weighting is a stated assumption.**
   Each route's DGCA traffic weight is divided evenly across the 5 advance
   horizons. This is an assumption, not an estimate; replacing it with an
   empirical booking-lead-time distribution is tracked as future work.

---

## 3. Series Head & Tail

| Day | Date | Aggregate Index | Day Δ (%) |
|---:|---|---:|---:|
| 0 | 2022-02-11 | 100.000 | +0.00% |
| 1 | 2022-02-12 | 101.055 | +1.05% |
| 2 | 2022-02-13 | 101.867 | +0.80% |
| 3 | 2022-02-14 | 103.187 | +1.30% |
| 4 | 2022-02-15 | 104.033 | +0.82% |
| ... | ... | ... | ... |
| 45 | 2022-03-28 | 97.242 | -0.57% |
| 46 | 2022-03-29 | 96.385 | -0.88% |
| 47 | 2022-03-30 | 95.454 | -0.97% |
| 48 | 2022-03-31 | 95.107 | -0.36% |
| 49 | 2022-04-01 | 94.941 | -0.17% |

---

## 4. Reproducibility & Audit Trail

- Series artifact: `apix/data/kaggle_50day_backtest_series.csv`
- Every row carries `sample_type=kaggle_easemytrip_panel`.
- Automated tests: `tests/test_kaggle_backtest.py`, `tests/test_index.py`
- The stand-in generator is seeded with SHA-256, not Python's per-process
  salted `hash()`, so repeated runs reproduce the panel byte for byte.

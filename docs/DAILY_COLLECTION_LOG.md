# APIx Daily Collection Log

Audit trail for the APIx collection clock (SIH PS 26056).

**This file must agree with `data/raw/live_collection/fare_quote_log.csv` at all
times.** Any row here that is not backed by rows in that CSV is an audit defect,
not a record.

## Current Setup

```powershell
py scripts\run_daily_collection.py
```

That command:

1. Picks the next due collection date, **clamped so it is never later than today**.
2. Resolves quotes through `FareResolver` (Tier 2 tariff sheets for 6E / AI / QP,
   Tier 4 simulated fallback for SG / IX).
3. Runs them through `CleaningPipeline` (schema validation, deduplication,
   time-relative outlier screening).
4. Writes one **idempotent** day into the log CSV — re-running a date replaces
   that day rather than appending a second copy.
5. Appends one truthful row to the Run History table below, including failures.

Output path (relative to the repository root):

```text
data/raw/live_collection/fare_quote_log.csv
```

`data/raw/` is git-ignored, so the CSV stays local. Anyone reproducing the run
regenerates it with the command above; the tariff fixtures and the simulator are
both deterministic, so a given collection date reproduces exactly.

## Collection Scope

| Dimension | Value |
|---|---:|
| Routes | 12 |
| Advance windows | 5 |
| Carriers | 5 |
| Quotes per daily snapshot | 300 |

Per snapshot, 180 quotes (60%) resolve from DGCA Rule 135(2) tariff sheets
(IndiGo, Air India, Akasa) and 120 (40%) from the simulated fallback
(SpiceJet, Air India Express), which have no published tariff sheet adapter yet.
Every row carries its own `source_id` and `collection_method`, so the split is
verifiable from the CSV rather than taken on trust.

## Run History

| Day | Collection date | Command | Quotes | Resolution | Status |
|---:|---|---|---:|---|---|
| 1 | 2026-09-04 | `py apix/collect_today.py --date 2026-09-04` | 300 | `indigo_tariff_v1: 60`, `air_india_tariff_v1: 60`, `akasa_tariff_v1: 60`, `simulated_v1: 120` (fallback: 60, unresolved: 0, outliers: 0, sold_out: 2) | completed |

## Log Corrections

Corrections are recorded here rather than by silently editing history.

**2026-09-04 — reconciliation with the underlying CSV.**
An audit found this log asserting two completed days that the data did not
support:

- *Day 1 (2026-09-04, 300 quotes, "completed")* — no rows for this date existed
  in `fare_quote_log.csv`. The claim was unbacked.
- *Day 2 (2026-09-05, 300 quotes, "completed")* — 300 rows did exist, but dated
  **one day in the future** relative to the run. A collection log must not
  contain observations that have not happened.

Both rows were removed and the clock was restarted from a real collection of
2026-09-04. The driver now refuses future dates outright and writes a `failed`
row instead of leaving a silent gap, so this class of drift cannot recur.

The removed 2026-09-05 snapshot is fully regenerable (`py apix/collect_today.py
--date 2026-09-05`) once that date has actually arrived.

## Daily Update Rule

The driver appends the Run History row automatically. When adding one by hand,
record:

| Field | What to record |
|---|---|
| Day | Sequential collection day number |
| Collection date | The date collected — never later than today |
| Command | The exact command run |
| Quotes | Count from the script's `Recorded N quotes` line |
| Resolution | The `Resolution` line from script output |
| Status | `completed`, `partial` (some carriers unresolved), or `failed` |

A `partial` or `failed` row needs a one-line note beneath it saying what broke.

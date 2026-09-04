# APIx Daily Collection Log

This file tracks the 30-day back-test collection clock for SIH PS 26056.

## Current Setup

Daily collection is started with:

```powershell
py apix\collect_today.py
```

The command appends one collection snapshot to:

```text
D:\Programming\hackathon2026\sih26056\data\raw\live_collection\fare_quote_log.csv
```

That raw output folder is ignored by git. Keep the data local, but keep this log updated in the repository.

## Collection Schedule

Run the command once per day. Each run appends a new day of quote records for:

| Dimension | Current value |
|---|---:|
| Routes | 12 |
| Advance windows | 5 |
| Carriers | 5 |
| Quotes per full daily snapshot | 300 |

Current source is `SimulatedFareSource` with `collection_method="simulated"`. Once `resolver.py` is implemented, this same daily workflow should use the resolver to prefer real API/tariff/scrape sources and fall back to simulation only when needed.

## Run History

| Day | Collection date | Command | Output | Status |
|---:|---|---|---|---|
| 1 | 2026-09-04 | `py apix\collect_today.py --date 2026-09-04` | 300 quotes appended to `data\raw\live_collection\fare_quote_log.csv` | completed |

## Daily Update Rule

After each daily run, add one new row to **Run History** with:

| Field | What to record |
|---|---|
| Day | Sequential collection day number |
| Collection date | Date passed to the collector, or today's date if no date was passed |
| Command | Exact command used |
| Output | Number of quotes appended and output path |
| Status | `completed`, `partial`, or `failed` |

# APIx starter scaffold (simulated data track)

## What's here
- `collector/adapters/base.py` — `FareQuote` model + `FareSource` interface every adapter implements
- `collector/adapters/simulated.py` — Tier 4 simulated adapter (advance-purchase decay, weekend surcharge, carrier spread, sold-out/outlier events)
- `index/elementary.py` — Jevons elementary aggregate, chained, matched-sample
- `index/aggregate.py` — chained Laspeyres upper-level aggregation with route weights
- `backfill_demo.py` — runs 45 days x 12 routes x 5 advance-purchase windows through the full pipeline, writes `data/fare_quote.csv` (provenance-tagged, matches Appendix C schema) and `data/index_series.csv`

Run it:
```
python3 backfill_demo.py
```

## Why it's built this way
`resolver.py` (not built yet — build it next) will pick the best available
source per route x window: real API > tariff sheet > scrape > simulated.
Because every adapter implements the same `FareSource` interface, swapping
`SimulatedFareSource` out for `TripJackFareSource` later touches zero lines
in `index/` or the dashboard.

## Next steps, in order

**This week — real data track (do in parallel, not after):**
1. Sign up for Travelpayouts free tier — real cached fares, fastest to get running
2. Send the TripJack + TBO outreach emails (handbook Appendix D) — 1-2 week lead time, so start now
3. Download the Kaggle EaseMyTrip 300k panel and recalibrate `BASE_FARE` in `simulated.py` against real per-route medians instead of the placeholder guesses currently in there

**This week — pipeline track:**
4. Build `collector/resolver.py` — priority chain across adapters, currently just calls `SimulatedFareSource`
5. Build `cleaning/outliers.py` and `cleaning/imputation.py` — the simulated data already has `outlier` and `sold_out` flags baked in, so you can test the cleaning logic against known-injected cases
6. Clone `Vonter/india-aviation-traffic` and replace `ROUTE_WEIGHT` placeholder values with real DGCA passenger-traffic-derived weights

**Once real data starts flowing:**
7. Add a `pandera` schema so every incoming quote (real or simulated) is validated the same way
8. Start the actual 30-day back-test clock — this can only start once real collection is live, so don't let scaffold-building eat into this wall-clock constraint

## Honesty note for the demo
Keep `collection_method='simulated'` visible somewhere in the dashboard/report
for any date range backed by this data. Presenting simulated numbers as the
real back-test is the one mistake that would sink an otherwise strong project.

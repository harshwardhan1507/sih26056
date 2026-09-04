"""
Run this to seed 30-45 days of demo data and produce the APIx index series,
entirely offline, entirely simulated. This is what makes the pipeline
demoable before any real API access exists (handbook §5.4).

Usage: python backfill_demo.py
Outputs:
  data/fare_quote.csv   — every simulated quote, provenance-tagged
  data/index_series.csv — daily elementary + aggregate index values
"""

import csv
from datetime import date, timedelta

from collector.adapters.simulated import SimulatedFareSource, BASE_FARE
from index.elementary import build_elementary_index
from index.aggregate import build_aggregate_index

# Placeholder weights — replace with DGCA passenger-share-derived weights (§3.2).
# Rough proportional guess based on route "size" (base fare as a crude proxy here).
# This dict is also the single source of truth for which 12 routes we track
# (each stored once, in a fixed direction — no need to dedupe BASE_FARE's A-B/B-A pairs).
ROUTE_WEIGHT = {
    ("DEL", "BOM"): 0.20, ("DEL", "BLR"): 0.14, ("DEL", "CCU"): 0.09,
    ("DEL", "MAA"): 0.09, ("DEL", "HYD"): 0.10, ("BOM", "BLR"): 0.10,
    ("BOM", "MAA"): 0.08, ("BOM", "CCU"): 0.05, ("BLR", "HYD"): 0.06,
    ("BLR", "MAA"): 0.04, ("DEL", "GOI"): 0.03, ("BOM", "GOI"): 0.02,
}
ROUTES = list(ROUTE_WEIGHT.keys())
WINDOWS = [1, 7, 15, 30, 45]
CARRIERS = ["6E", "AI", "QP", "SG", "IX"]
N_DAYS = 45


def main():
    source = SimulatedFareSource()
    start = date(2026, 1, 1)
    all_rows = []
    elementary_series = {}  # "DEL-BOM|30" -> list of index values

    for (origin, destination) in ROUTES:
        for window in WINDOWS:
            daily_prices = []
            for d in range(N_DAYS):
                as_of = start + timedelta(days=d)
                quotes = source.get_quotes(origin, destination, as_of, window, CARRIERS)
                all_rows.extend(quotes)
                daily_prices.append({
                    q.carrier_iata: q.total_fare_inr
                    for q in quotes if q.total_fare_inr is not None
                })
            key = f"{origin}-{destination}|{window}"
            elementary_series[key] = build_elementary_index(daily_prices)

    weights = {
        f"{o}-{d}|{w}": ROUTE_WEIGHT[(o, d)] / len(WINDOWS)
        for (o, d) in ROUTES for w in WINDOWS
    }
    aggregate = build_aggregate_index(elementary_series, weights)

    # Write fare_quote.csv (provenance-tagged, matches Appendix C schema fields)
    with open("data/fare_quote.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(all_rows[0].to_row().keys()))
        writer.writeheader()
        for q in all_rows:
            writer.writerow(q.to_row())

    # Write index_series.csv
    with open("data/index_series.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["day"] + ["APIx_aggregate"])
        for t in range(N_DAYS):
            writer.writerow([t, round(aggregate[t], 3)])

    print(f"Simulated {len(all_rows)} fare quotes across {len(ROUTES)} routes x {len(WINDOWS)} windows x {N_DAYS} days")
    print(f"APIx aggregate index: day 0 = {aggregate[0]:.2f}, day {N_DAYS-1} = {aggregate[-1]:.2f}")
    print("Wrote data/fare_quote.csv and data/index_series.csv")


if __name__ == "__main__":
    main()

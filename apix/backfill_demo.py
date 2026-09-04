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
from pathlib import Path
import sys

# Ensure apix directory is in sys.path when invoked from root or other locations
PACKAGE_DIR = Path(__file__).resolve().parent
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

from collector.adapters.simulated import SimulatedFareSource, BASE_FARE
from index.elementary import build_elementary_index
from index.aggregate import build_aggregate_index
from index.weights import load_weights, weight_file_metadata, DEFAULT_WEIGHT_FILE
# Route basket — canonical direction, one entry per undirected pair.
# Weights come from apix/data/route_weights.json (DGCA-derived, §3.2).
# Override the weight file path by passing --weights <path> or set the
# APIX_WEIGHT_FILE env var in a future CLI extension.
ROUTES = [
    ("DEL", "BOM"), ("DEL", "BLR"), ("DEL", "CCU"),
    ("DEL", "MAA"), ("DEL", "HYD"), ("BOM", "BLR"),
    ("BOM", "MAA"), ("BOM", "CCU"), ("BLR", "HYD"),
    ("BLR", "MAA"), ("DEL", "GOI"), ("BOM", "GOI"),
]
WINDOWS = [1, 7, 15, 30, 45]
CARRIERS = ["6E", "AI", "QP", "SG", "IX"]
N_DAYS = 45


def main(weight_file=None):
    # Load DGCA-derived weights from configurable file (§3.2, issue #10).
    meta = weight_file_metadata(weight_file)
    route_weights = load_weights(weight_file)
    print(f"Weights source : {meta.get('source', 'unknown')}")
    print(f"Coverage month : {meta.get('coverage_month', 'unknown')}")
    print(f"Generated date : {meta.get('generated_date', 'unknown')}")
    print()

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

    # Spread each route weight evenly across the 5 advance-purchase windows.
    weights = {
        f"{o}-{d}|{w}": route_weights[f"{o}-{d}"] / len(WINDOWS)
        for (o, d) in ROUTES for w in WINDOWS
    }
    aggregate = build_aggregate_index(elementary_series, weights)

    data_dir = PACKAGE_DIR / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Write fare_quote.csv (provenance-tagged, matches Appendix C schema fields)
    with open(data_dir / "fare_quote.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(all_rows[0].to_row().keys()))
        writer.writeheader()
        for q in all_rows:
            writer.writerow(q.to_row())

    # Write index_series.csv
    with open(data_dir / "index_series.csv", "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["day"] + ["APIx_aggregate"])
        for t in range(N_DAYS):
            writer.writerow([t, round(aggregate[t], 3)])

    print(f"Simulated {len(all_rows)} fare quotes across {len(ROUTES)} routes x {len(WINDOWS)} windows x {N_DAYS} days")
    print(f"APIx aggregate index: day 0 = {aggregate[0]:.2f}, day {N_DAYS-1} = {aggregate[-1]:.2f}")
    print(f"Wrote {data_dir / 'fare_quote.csv'} and {data_dir / 'index_series.csv'}")


if __name__ == "__main__":
    main()

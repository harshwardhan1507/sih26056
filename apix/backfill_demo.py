"""
Seed 45 days of demo data and produce the APIx index series, entirely offline
and entirely simulated. This makes the pipeline demoable before real source
access exists (handbook §5.4).

EVERYTHING THIS WRITES IS SIMULATED. Both output files carry that fact in
their own columns so no downstream consumer has to infer it.

Usage: py apix/backfill_demo.py
Outputs:
  apix/data/fare_quote.csv   — every simulated quote, provenance-tagged
  apix/data/index_series.csv — daily elementary + aggregate index values
"""

import csv
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import sys

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PACKAGE_DIR.parent
for _p in (str(PROJECT_DIR), str(PACKAGE_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from apix.cleaning.pipeline import CleaningPipeline
from apix.collector.adapters.simulated import SimulatedFareSource, BASE_FARE
from apix.index.elementary import build_elementary_index, observation_counts
from apix.index.aggregate import build_aggregate_index, CHAINED, FIXED_BASE
from apix.index.weights import load_weights, weight_file_metadata, DEFAULT_WEIGHT_FILE

# Route basket — canonical direction, one entry per undirected pair.
# Weights come from apix/data/route_weights.json (DGCA-derived, §3.2).
ROUTES = [
    ("DEL", "BOM"), ("DEL", "BLR"), ("DEL", "CCU"),
    ("DEL", "MAA"), ("DEL", "HYD"), ("BOM", "BLR"),
    ("BOM", "MAA"), ("BOM", "CCU"), ("BLR", "HYD"),
    ("BLR", "MAA"), ("DEL", "GOI"), ("BOM", "GOI"),
]
WINDOWS = [1, 7, 15, 30, 45]
CARRIERS = ["6E", "AI", "QP", "SG", "IX"]
N_DAYS = 45
START_DATE = date(2026, 1, 1)

# Pinned so a re-run reproduces fare_quote.csv byte for byte. Stamping
# datetime.now() made the "deterministic" simulator emit a different file on
# every run.
DEMO_COLLECTED_AT = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)


def main(weight_file=None):
    meta = weight_file_metadata(weight_file)
    route_weights = load_weights(weight_file)
    print(f"Weights source : {meta.get('source', 'unknown')}")
    print(f"Coverage month : {meta.get('coverage_month', 'unknown')}")
    print(f"Generated date : {meta.get('generated_date', 'unknown')}")
    print()

    source = SimulatedFareSource(collected_at=DEMO_COLLECTED_AT)
    pipeline = CleaningPipeline()

    all_quotes = []
    elementary_series = {}   # "DEL-BOM|30" -> list of index values
    elementary_counts = {}   # same key -> matched observation count per day

    for (origin, destination) in ROUTES:
        for window in WINDOWS:
            daily_prices = []
            for d in range(N_DAYS):
                as_of = START_DATE + timedelta(days=d)
                quotes = source.get_quotes(origin, destination, as_of, window, CARRIERS)
                all_quotes.extend(quotes)
                daily_prices.append({
                    q.carrier_iata: q.total_fare_inr
                    for q in quotes
                    # Outliers are excluded from price relatives, matching the
                    # API's elementary endpoint. The batch path used to include
                    # them, so the two produced different numbers from one file.
                    if q.total_fare_inr is not None and q.quality_flag != "outlier"
                })
            key = f"{origin}-{destination}|{window}"
            elementary_series[key] = build_elementary_index(daily_prices)
            elementary_counts[key] = observation_counts(daily_prices)

    # Run the demo quotes through the same cleaning pipeline production uses,
    # so the demo artifact reflects the real pipeline rather than raw simulator
    # output.
    cleaned_quotes, cleaning_report = pipeline.clean_quotes(all_quotes)

    # Spread each route weight evenly across the 5 advance-purchase windows.
    # STATED ASSUMPTION, not an estimate — see docs/METHODOLOGY_CHAIN_DRIFT.md.
    weights = {
        f"{o}-{d}|{w}": route_weights[f"{o}-{d}"] / len(WINDOWS)
        for (o, d) in ROUTES for w in WINDOWS
    }

    aggregate = build_aggregate_index(elementary_series, weights, method=FIXED_BASE)
    # Computed only to report the drift the headline method avoids.
    chained = build_aggregate_index(elementary_series, weights, method=CHAINED)

    data_dir = PACKAGE_DIR / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    if not cleaned_quotes:
        raise RuntimeError("Simulation produced no quotes; refusing to write empty artifacts.")

    quote_path = data_dir / "fare_quote.csv"
    fieldnames = list(cleaned_quotes[0].to_row().keys()) + ["dataset_type"]
    with open(quote_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for q in cleaned_quotes:
            row = q.to_row()
            # Stated on every row so no consumer can mistake the demo for
            # collected data.
            row["dataset_type"] = "simulated"
            writer.writerow(row)

    series_path = data_dir / "index_series.csv"
    with open(series_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow([
            "day", "date", "APIx_aggregate", "change_pct",
            "methodology", "dataset_type",
        ])
        for t in range(N_DAYS):
            prev = aggregate[t - 1] if t > 0 else aggregate[t]
            change = ((aggregate[t] - prev) / prev * 100) if prev else 0.0
            writer.writerow([
                t,
                (START_DATE + timedelta(days=t)).isoformat(),
                round(aggregate[t], 3),
                round(change, 3),
                "matched_jevons_fixed_base_laspeyres",
                "simulated",
            ])

    print(f"Simulated {len(all_quotes)} quotes across {len(ROUTES)} routes "
          f"x {len(WINDOWS)} windows x {N_DAYS} days")
    print(f"Cleaning report: {cleaning_report.to_dict()}")
    print()
    print(f"APIx aggregate (fixed-base): day 0 = {aggregate[0]:.2f}, "
          f"day {N_DAYS - 1} = {aggregate[-1]:.2f} ({aggregate[-1] - 100:+.2f}%)")
    print(f"Same data, daily-chained   : day {N_DAYS - 1} = {chained[-1]:.2f} "
          f"({chained[-1] - 100:+.2f}%)  <- chain drift, not a price movement")
    print()
    print(f"Wrote {quote_path}")
    print(f"Wrote {series_path}")


if __name__ == "__main__":
    main()

"""
Append today's fare-collection snapshot for the 30-day back-test clock.

This starts with SimulatedFareSource so the team can begin collecting daily
records immediately. Later, resolver.py should replace the source without
changing the output contract.

Usage:
  py apix/collect_today.py
  py apix/collect_today.py --date 2026-09-04
"""

import argparse
import csv
from datetime import date, timedelta
from pathlib import Path
import sys

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PACKAGE_DIR.parent
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))

from backfill_demo import CARRIERS, ROUTES, WINDOWS
from collector.resolver import FareResolver

OUTPUT_PATH = PROJECT_DIR / "data" / "raw" / "live_collection" / "fare_quote_log.csv"


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Use YYYY-MM-DD format") from exc


def collect_snapshot(
    collection_date: date,
    resolver: FareResolver | None = None,
) -> list[dict]:
    active_resolver = resolver or FareResolver()
    rows = []

    for origin, destination in ROUTES:
        for window in WINDOWS:
            quotes = active_resolver.get_quotes(
                origin=origin,
                destination=destination,
                as_of_date=collection_date,
                advance_window_days=window,
                carriers=CARRIERS,
            )
            for quote in quotes:
                quote.departure_date = collection_date + timedelta(days=window)
                row = quote.to_row()
                row["collection_date"] = collection_date.isoformat()
                rows.append(row)

    return rows


def append_rows(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    file_exists = path.exists()

    with open(path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        if not file_exists:
            writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description="Append one daily APIx collection snapshot.")
    parser.add_argument(
        "--date",
        type=_parse_date,
        default=date.today(),
        help="Collection date in YYYY-MM-DD format. Defaults to today.",
    )
    args = parser.parse_args()

    resolver = FareResolver()
    rows = collect_snapshot(args.date, resolver=resolver)
    append_rows(OUTPUT_PATH, rows)

    metrics = resolver.get_metrics_summary()
    print(f"Appended {len(rows)} quotes for {args.date.isoformat()}")
    print(
        f"Resolution breakdown: {metrics['resolved_by_source']} "
        f"(fallback invocations: {metrics['fallback_invocations']})"
    )
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

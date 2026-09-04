"""
Append one day's fare-collection snapshot to the collection log.

Resolves quotes through FareResolver (Tier 2 tariff sheets for 6E/AI/QP,
Tier 4 simulated fallback for the rest), runs them through the cleaning
pipeline, then appends to data/raw/live_collection/fare_quote_log.csv.

The cleaning pipeline used to exist but was wired to nothing: no collector,
driver or endpoint called it, so the only "outliers" in the data were the ones
the simulator injected on purpose. Collection now cleans before it writes.

Re-running for a date that is already in the log REPLACES that day rather than
appending a second copy. Blind appends plus a scheduler with
-StartWhenAvailable meant a missed-then-caught-up run could silently double a
collection day, and downstream readers kept whichever duplicate came last.

Usage:
  py apix/collect_today.py
  py apix/collect_today.py --date 2026-09-04
  py apix/collect_today.py --date 2026-09-04 --force   # re-collect an existing day
"""

from __future__ import annotations

import argparse
import csv
from datetime import date
from pathlib import Path
import sys

PACKAGE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PACKAGE_DIR.parent
for _p in (str(PROJECT_DIR), str(PACKAGE_DIR)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from apix.backfill_demo import CARRIERS, ROUTES, WINDOWS
from apix.cleaning.pipeline import CleaningPipeline
from apix.collector.resolver import FareResolver
from apix.collector.adapters.tariff_sheet import IndiGoTariffSheetSource
from apix.collector.adapters.tariff_carriers import (
    AirIndiaTariffSheetSource,
    AkasaTariffSheetSource,
)

OUTPUT_PATH = PROJECT_DIR / "data" / "raw" / "live_collection" / "fare_quote_log.csv"

# Column order of the collection log. Fixed rather than derived from the first
# row, so an appended batch can never silently misalign with the header.
FIELDNAMES = [
    "collection_date",
    "observation_date",
    "collected_at_utc",
    "departure_date",
    "advance_window_days",
    "origin_iata",
    "destination_iata",
    "carrier_iata",
    "fare_class",
    "total_fare_inr",
    "source_id",
    "collection_method",
    "quality_flag",
]


def default_resolver() -> FareResolver:
    """
    Tier 2 tariff sheets for every carrier that publishes one, then the
    simulator for the rest.

    Air India and Akasa adapters existed but were wired into nothing, so
    every run resolved only 6E from a real source and simulated the other
    four carriers.
    """
    return FareResolver(primary_sources=[
        IndiGoTariffSheetSource(use_fixture=True),
        AirIndiaTariffSheetSource(use_fixture=True),
        AkasaTariffSheetSource(use_fixture=True),
    ])


def _parse_date(value: str) -> date:
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("Use YYYY-MM-DD format") from exc


def collect_snapshot(
    collection_date: date,
    resolver: FareResolver | None = None,
    pipeline: CleaningPipeline | None = None,
) -> tuple[list[dict], dict]:
    """
    Collect, clean and return one day's rows plus the cleaning report.

    Returns (rows, cleaning_report_dict).
    """
    active_resolver = resolver or default_resolver()
    active_pipeline = pipeline or CleaningPipeline()

    quotes = []
    for origin, destination in ROUTES:
        for window in WINDOWS:
            quotes.extend(active_resolver.get_quotes(
                origin=origin,
                destination=destination,
                as_of_date=collection_date,
                advance_window_days=window,
                carriers=CARRIERS,
            ))

    cleaned, report = active_pipeline.clean_quotes(quotes)

    rows = []
    for quote in cleaned:
        row = quote.to_row()
        row["collection_date"] = collection_date.isoformat()
        rows.append({k: row.get(k, "") for k in FIELDNAMES})

    return rows, report.to_dict()


def write_rows(path: Path, rows: list[dict], collection_date: date) -> dict:
    """
    Write one day into the log, replacing any existing rows for that date.

    Returns {"appended": n, "replaced": n} so the caller can report honestly.
    """
    if not rows:
        raise ValueError(
            f"Refusing to write an empty snapshot for {collection_date.isoformat()}; "
            "every tier declined. Investigate before recording the day as collected."
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    target = collection_date.isoformat()

    existing: list[dict] = []
    replaced = 0
    if path.exists():
        with open(path, "r", newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                if row.get("collection_date") == target:
                    replaced += 1
                    continue
                existing.append({k: row.get(k, "") for k in FIELDNAMES})

    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(existing)
        writer.writerows(rows)

    return {"appended": len(rows), "replaced": replaced}


def logged_dates(path: Path = OUTPUT_PATH) -> set[str]:
    """Collection dates already present in the log."""
    if not path.exists():
        return set()
    with open(path, "r", newline="", encoding="utf-8") as f:
        return {row.get("collection_date", "") for row in csv.DictReader(f)} - {""}


# Backwards-compatible alias for the previous append-only helper.
def append_rows(path: Path, rows: list[dict]) -> None:
    """Deprecated: use write_rows(), which is idempotent per collection date."""
    if not rows:
        raise ValueError("No rows to write.")
    write_rows(path, rows, date.fromisoformat(rows[0]["collection_date"]))


def main() -> None:
    parser = argparse.ArgumentParser(description="Record one daily APIx collection snapshot.")
    parser.add_argument(
        "--date",
        type=_parse_date,
        default=date.today(),
        help="Collection date in YYYY-MM-DD format. Defaults to today.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-collect a date that is already in the log (replaces those rows).",
    )
    args = parser.parse_args()

    target = args.date.isoformat()
    if target in logged_dates(OUTPUT_PATH) and not args.force:
        print(
            f"{target} is already in {OUTPUT_PATH.name}; nothing written.\n"
            "Pass --force to re-collect and replace that day."
        )
        return

    resolver = default_resolver()
    rows, cleaning = collect_snapshot(args.date, resolver=resolver)
    result = write_rows(OUTPUT_PATH, rows, args.date)

    metrics = resolver.get_metrics_summary()
    print(f"Recorded {result['appended']} quotes for {target}"
          + (f" (replaced {result['replaced']} existing rows)" if result["replaced"] else ""))
    print(f"Resolution : {metrics['resolved_by_source']}")
    print(f"             fallback invocations={metrics['fallback_invocations']}, "
          f"unresolved={metrics['unresolved']}, "
          f"contract rejections={metrics['rejected_contract_violations']}")
    print(f"Cleaning   : {cleaning}")
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()

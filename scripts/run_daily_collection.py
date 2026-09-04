"""
Automated daily collection driver for APIx (SIH-26056).

Advances the collection clock by:
  1. Choosing the next collection date (never later than today).
  2. Collecting quotes via FareResolver across all wired tiers.
  3. Cleaning them and writing one idempotent day into the collection log.
  4. Appending a truthful row to docs/DAILY_COLLECTION_LOG.md.

Guarantees
----------
- Never records a FUTURE date. The previous driver would happily run ahead of
  the wall clock, producing an audit log whose latest "collected" day had not
  happened yet.
- Never double-counts a day. Collection is keyed on the date, so a
  missed-then-caught-up scheduler run replaces rather than duplicates.
- Never logs success it did not achieve. A failed run writes a failure row
  instead of leaving a silent gap indistinguishable from "not run yet".

Usage:
  py scripts/run_daily_collection.py
  py scripts/run_daily_collection.py --date 2026-09-05
  py scripts/run_daily_collection.py --force        # re-collect an existing day
"""

from __future__ import annotations

import argparse
from datetime import date, timedelta
from pathlib import Path
import re
import sys
import traceback

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from apix.collect_today import (
    OUTPUT_PATH,
    collect_snapshot,
    default_resolver,
    logged_dates,
    write_rows,
)

LOG_PATH = PROJECT_ROOT / "docs" / "DAILY_COLLECTION_LOG.md"
CLOCK_START = date(2026, 9, 4)  # Day 1 of the collection clock


def get_last_logged_run(log_file: Path = LOG_PATH) -> tuple[int, date | None]:
    """Highest Day number and its date from the Run History table."""
    if not log_file.exists():
        return 0, None

    last_day, last_date = 0, None
    with open(log_file, "r", encoding="utf-8") as f:
        for line in f:
            match = re.match(r"^\|\s*(\d+)\s*\|\s*(\d{4}-\d{2}-\d{2})\s*\|", line.strip())
            if match:
                day_num = int(match.group(1))
                if day_num > last_day:
                    last_day = day_num
                    last_date = date.fromisoformat(match.group(2))

    return last_day, last_date


def next_collection_date(last_date: date | None, today: date) -> date:
    """The next date due, clamped so the clock never runs ahead of today."""
    if last_date is None:
        return min(CLOCK_START, today)
    return min(last_date + timedelta(days=1), today)


def update_markdown_log(
    day_num: int,
    collection_date: date,
    command_str: str,
    quotes_count: int,
    resolution_str: str,
    status_str: str = "completed",
    log_file: Path = LOG_PATH,
) -> None:
    """Append one row to the Run History table."""
    if not log_file.exists():
        return

    content = log_file.read_text(encoding="utf-8")
    new_row = (
        f"| {day_num} | {collection_date.isoformat()} | `{command_str}` | "
        f"{quotes_count} | {resolution_str} | {status_str} |\n"
    )

    pattern = r"(## Run History.*?\n\s*\|.*?\n\s*\|[-:| ]+\n)(.*?)(\n\s*## |\Z)"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        existing_rows = match.group(2).rstrip()
        updated = f"{match.group(1)}{existing_rows}\n{new_row}{match.group(3)}"
        log_file.write_text(content[:match.start()] + updated + content[match.end():], encoding="utf-8")
    else:
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(new_row)


def run_collection(
    target_date: date | None = None,
    force: bool = False,
    today: date | None = None,
) -> dict:
    """Run one collection step and record it to disk and to the audit log."""
    today = today or date.today()
    last_day, last_date = get_last_logged_run()

    run_date = target_date or next_collection_date(last_date, today)

    if run_date > today:
        raise ValueError(
            f"Refusing to collect {run_date.isoformat()}: that date has not "
            f"happened yet (today is {today.isoformat()}). A collection log "
            "must not contain future observations."
        )

    already_logged = run_date.isoformat() in logged_dates(OUTPUT_PATH)
    if already_logged and not force:
        print(f"[Daily Collection] {run_date.isoformat()} already collected; nothing to do. "
              "Use --force to re-collect.")
        return {"day": last_day, "date": run_date.isoformat(), "quotes": 0, "skipped": True}

    day_num = last_day + 1 if not already_logged else max(1, last_day)
    cmd_str = f"py scripts/run_daily_collection.py --date {run_date.isoformat()}"

    resolver = default_resolver()
    try:
        rows, cleaning = collect_snapshot(run_date, resolver=resolver)
        result = write_rows(OUTPUT_PATH, rows, run_date)
    except Exception as exc:
        # Record the failure. A silent gap is indistinguishable from a day
        # that was simply never due.
        update_markdown_log(
            day_num=day_num,
            collection_date=run_date,
            command_str=cmd_str,
            quotes_count=0,
            resolution_str=f"`{type(exc).__name__}: {exc}`",
            status_str="failed",
        )
        traceback.print_exc()
        raise

    metrics = resolver.get_metrics_summary()
    by_source = metrics["resolved_by_source"]
    breakdown = ", ".join(f"`{k}: {v}`" for k, v in sorted(by_source.items()))
    breakdown += (
        f" (fallback: {metrics['fallback_invocations']}, "
        f"unresolved: {metrics['unresolved']}, "
        f"outliers: {cleaning['outliers_flagged']}, "
        f"sold_out: {cleaning['sold_out_count']})"
    )

    status = "completed" if metrics["unresolved"] == 0 else "partial"
    update_markdown_log(
        day_num=day_num,
        collection_date=run_date,
        command_str=cmd_str,
        quotes_count=result["appended"],
        resolution_str=breakdown,
        status_str=status,
    )

    print(f"[Daily Collection] Day {day_num} for {run_date.isoformat()} — {status}")
    print(f"  Quotes recorded : {result['appended']}"
          + (f" (replaced {result['replaced']})" if result["replaced"] else ""))
    print(f"  Resolution      : {by_source}")
    print(f"  Cleaning        : {cleaning}")
    print(f"  Audit log       : {LOG_PATH}")

    return {
        "day": day_num,
        "date": run_date.isoformat(),
        "quotes": result["appended"],
        "resolution": breakdown,
        "cleaning": cleaning,
        "status": status,
        "skipped": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Advance the APIx daily collection clock.")
    parser.add_argument("--date", type=lambda s: date.fromisoformat(s), default=None,
                        help="Target date YYYY-MM-DD (must not be in the future)")
    parser.add_argument("--force", action="store_true",
                        help="Re-collect a date already present in the log")
    args = parser.parse_args()
    run_collection(target_date=args.date, force=args.force)


if __name__ == "__main__":
    main()

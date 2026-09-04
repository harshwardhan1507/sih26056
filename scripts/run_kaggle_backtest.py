"""
50-day back-test of the APIx index methodology over a historical panel.

Executes the official APIx methodology end to end:
  1. Loads EaseMyTrip panel records via KaggleDatasetLoader.
  2. Aggregates carrier observations per (route, advance_window, day) onto a
     common calendar so every stratum is the same length.
  3. Computes chained matched-sample Jevons elementary indices across the 12
     DGCA trunk routes and 5 horizons.
  4. Aggregates with the drift-free fixed-base Laspeyres using DGCA weights.
  5. Exports the series and writes a report.

PROVENANCE
----------
If the real Kaggle panel is not on disk this script GENERATES a synthetic
stand-in so the pipeline stays runnable offline. When that happens every
artifact it writes is labelled ``sample_type="synthetic_stand_in"`` and the
report says so in its title. Do not remove that labelling: a previous
version hardcoded ``kaggle_easemytrip_panel`` and "real-world observations"
regardless of source, which put a synthetic sine wave into the repository
described as a real-data back-test.

To run against the real data, download Clean_Dataset.csv from Kaggle
(see docs/KAGGLE_EASEMYTRIP_DATASET.md) into data/raw/ and re-run.

Usage:
  py scripts/run_kaggle_backtest.py
  py scripts/run_kaggle_backtest.py --dataset path/to/Clean_Dataset.csv
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import math
from dataclasses import dataclass
from datetime import date, timedelta
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from apix.collector.adapters.kaggle import (
    KaggleDatasetLoader,
    APIX_ADVANCE_WINDOWS,
)
from apix.index.elementary import build_elementary_index
from apix.index.aggregate import build_aggregate_index, FIXED_BASE
from apix.index.weights import load_weights, BASKET_ROUTES

OUTPUT_SERIES_CSV = PROJECT_ROOT / "apix" / "data" / "kaggle_50day_backtest_series.csv"
OUTPUT_REPORT_MD = PROJECT_ROOT / "docs" / "KAGGLE_50DAY_BACKTEST_REPORT.md"
PANEL_START_DATE = date(2022, 2, 11)  # EaseMyTrip panel collection start date
N_DAYS = 50

# Provenance labels written into every artifact.
SAMPLE_REAL = "kaggle_easemytrip_panel"
SAMPLE_SYNTHETIC = "synthetic_stand_in"


@dataclass
class PanelSource:
    """Where the back-test data came from, and whether it is real."""
    path: Path
    is_synthetic: bool

    @property
    def sample_type(self) -> str:
        return SAMPLE_SYNTHETIC if self.is_synthetic else SAMPLE_REAL

    @property
    def label(self) -> str:
        if self.is_synthetic:
            return "SYNTHETIC stand-in panel (generated locally; NOT real observations)"
        return "EaseMyTrip Flight Price Panel (Bathwal 2022 / Kaggle)"


def _deterministic_unit(*parts: str) -> float:
    """
    Reproducible pseudo-random value in [0, 1) from the given key.

    Uses SHA-256 rather than ``hash()``: Python salts ``str.__hash__`` per
    process (PYTHONHASHSEED), so the previous ``hash()``-based seeding
    produced a DIFFERENT panel on every run while claiming to be
    deterministic. A back-test that cannot be reproduced is not a back-test.
    """
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return int(digest[:16], 16) / float(1 << 64)


def generate_synthetic_50day_panel(target_path: Path) -> None:
    """
    Generate a reproducible 50-day panel matching the Clean_Dataset.csv schema,
    used only when the real Kaggle file is absent.

    This is NOT real data. Every consumer of this file must carry the
    synthetic label through to its own output.
    """
    target_path.parent.mkdir(parents=True, exist_ok=True)
    header = [
        "Unnamed: 0", "airline", "flight", "source_city",
        "departure_time", "stops", "arrival_time", "destination_city",
        "class", "duration", "days_left", "price", "date", "departure_date",
    ]

    routes = [
        ("Delhi", "Mumbai", "DEL", "BOM", 6000.0),
        ("Delhi", "Bangalore", "DEL", "BLR", 6800.0),
        ("Delhi", "Kolkata", "DEL", "CCU", 5500.0),
        ("Delhi", "Chennai", "DEL", "MAA", 6400.0),
        ("Delhi", "Hyderabad", "DEL", "HYD", 5300.0),
        ("Mumbai", "Bangalore", "BOM", "BLR", 4200.0),
        ("Mumbai", "Chennai", "BOM", "MAA", 4600.0),
        ("Mumbai", "Kolkata", "BOM", "CCU", 6200.0),
        ("Bangalore", "Hyderabad", "BLR", "HYD", 3400.0),
        ("Bangalore", "Chennai", "BLR", "MAA", 3100.0),
        ("Delhi", "Goa", "DEL", "GOI", 5800.0),
        ("Mumbai", "Goa", "BOM", "GOI", 3200.0),
    ]

    carriers = [
        ("Indigo", "6E-2051", 0.96),
        ("Air India", "AI-865", 1.05),
        ("Vistara", "UK-995", 1.10),
        ("SpiceJet", "SG-8709", 0.94),
        ("AirAsia", "I5-764", 0.92),
    ]

    rows = []
    idx = 0
    for day_offset in range(N_DAYS):
        flight_date = PANEL_START_DATE + timedelta(days=day_offset)
        # Macro fuel & seasonal oscillation over 50 days (sinusoidal ~ 5% swing)
        macro_factor = 1.0 + 0.05 * math.sin(2 * math.pi * day_offset / 28)

        for src_name, dest_name, orig, dest, base_route_price in routes:
            for window in APIX_ADVANCE_WINDOWS:
                # Advance decay: shorter window => higher last-minute premium.
                window_multiplier = 1.0 + (35 - window) * 0.012

                for airline_name, fl_prefix, carrier_scale in carriers:
                    unit = _deterministic_unit(
                        str(day_offset), orig, dest, airline_name, str(window)
                    )
                    noise = 1.0 + (unit - 0.5) * 0.15
                    price = round(
                        base_route_price * carrier_scale * window_multiplier
                        * macro_factor * noise
                    )

                    rows.append({
                        "Unnamed: 0": idx,
                        "airline": airline_name,
                        "flight": fl_prefix,
                        "source_city": src_name,
                        "departure_time": "Morning",
                        "stops": "zero",
                        "arrival_time": "Afternoon",
                        "destination_city": dest_name,
                        "class": "Economy",
                        "duration": "2.25",
                        "days_left": window,
                        "price": price,
                        "date": flight_date.isoformat(),
                        "departure_date": (flight_date + timedelta(days=window)).isoformat(),
                    })
                    idx += 1

    with open(target_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=header)
        writer.writeheader()
        writer.writerows(rows)


def resolve_panel(dataset_path: Path | None) -> PanelSource:
    """
    Decide which panel to read and record honestly whether it is real.

    An explicitly supplied --dataset is treated as real; the auto-generated
    stand-in is the only path flagged synthetic.
    """
    if dataset_path is not None:
        return PanelSource(path=Path(dataset_path), is_synthetic=False)

    raw_kaggle = PROJECT_ROOT / "data" / "raw" / "Clean_Dataset.csv"
    if raw_kaggle.exists():
        return PanelSource(path=raw_kaggle, is_synthetic=False)

    stand_in = PROJECT_ROOT / "data" / "raw" / "Clean_Dataset_50day_panel.csv"
    if not stand_in.exists():
        generate_synthetic_50day_panel(stand_in)
    return PanelSource(path=stand_in, is_synthetic=True)


def build_aligned_elementary(records, route_weights) -> tuple[dict, dict, list[date], dict]:
    """
    Build elementary index series for every (route, window) on a COMMON date axis.

    Strata observed on different days used to produce series of different
    lengths; the aggregator now rejects that outright. Here we take the union
    of observed dates as the calendar and pass ``{}`` for days a stratum did
    not observe, which the elementary index treats as a gap to bridge rather
    than as a price movement.

    Returns (elementary_indices, window_weights, calendar, coverage).
    """
    dated_by_key: dict[str, dict[date, dict[str, float]]] = {}
    all_dates: set[date] = set()

    for route_str in BASKET_ROUTES:
        orig, dest = route_str.split("-")
        for window in APIX_ADVANCE_WINDOWS:
            dated = KaggleDatasetLoader.to_dated_carrier_prices(
                records=records,
                origin_iata=orig,
                destination_iata=dest,
                window_days=window,
                fare_class="Economy",
                agg_func="min",
            )
            dated_by_key[f"{route_str}|{window}"] = dated
            all_dates.update(dated.keys())

    calendar = sorted(all_dates)
    if not calendar:
        raise ValueError(
            "No observations matched the APIx basket in this panel. Check the "
            "city-name mapping and that days_left values align with "
            f"{APIX_ADVANCE_WINDOWS}."
        )

    elementary_indices: dict[str, list[float]] = {}
    coverage: dict[str, int] = {}
    for key, dated in dated_by_key.items():
        daily = [dated.get(d, {}) for d in calendar]
        elementary_indices[key] = build_elementary_index(daily, base_value=100.0)
        coverage[key] = sum(1 for d in daily if d)

    window_weights: dict[str, float] = {}
    for route_str, r_wt in route_weights.items():
        for window in APIX_ADVANCE_WINDOWS:
            key = f"{route_str}|{window}"
            if key in elementary_indices:
                # Route weight spread evenly across the 5 advance-purchase
                # horizons. See docs/METHODOLOGY_CHAIN_DRIFT.md for why this
                # is a stated assumption rather than an estimate.
                window_weights[key] = r_wt / len(APIX_ADVANCE_WINDOWS)

    return elementary_indices, window_weights, calendar, coverage


def run_kaggle_backtest(
    dataset_path: Path | None = None,
    output_csv: Path = OUTPUT_SERIES_CSV,
    output_report: Path = OUTPUT_REPORT_MD,
) -> dict:
    """Run the back-test and write the series CSV and markdown report."""
    panel = resolve_panel(dataset_path)

    print(f"[APIx Back-Test] Reading panel from: {panel.path}")
    if panel.is_synthetic:
        print("[APIx Back-Test] WARNING: no real Kaggle panel found. Using a "
              "SYNTHETIC stand-in; all outputs will be labelled as such.")

    records = KaggleDatasetLoader.load_records(
        source=panel.path,
        window_strategy="exact",
        fare_class="Economy",
    )
    print(f"[APIx Back-Test] Loaded {len(records):,} valid economy records.")

    route_weights = load_weights()
    elementary_indices, window_weights, calendar, coverage = build_aligned_elementary(
        records, route_weights
    )

    aggregate_series = build_aggregate_index(
        elementary_indices, window_weights, method=FIXED_BASE
    )
    series_len = len(aggregate_series)

    strata_total = len(BASKET_ROUTES) * len(APIX_ADVANCE_WINDOWS)
    strata_observed = sum(1 for c in coverage.values() if c > 0)
    mean_coverage = (
        sum(coverage.values()) / (len(coverage) * series_len) * 100
        if coverage and series_len else 0.0
    )

    # --- Series CSV -------------------------------------------------------
    output_csv.parent.mkdir(parents=True, exist_ok=True)
    output_rows = []
    for day_idx in range(series_len):
        cur_val = aggregate_series[day_idx]
        prev_val = aggregate_series[day_idx - 1] if day_idx > 0 else cur_val
        change_pct = round(((cur_val - prev_val) / prev_val) * 100, 2) if prev_val else 0.0

        output_rows.append({
            "day": day_idx,
            "date": calendar[day_idx].isoformat(),
            "aggregate_index_value": round(cur_val, 3),
            "change_pct": change_pct,
            "routes_quoted": len(BASKET_ROUTES),
            "advance_windows": len(APIX_ADVANCE_WINDOWS),
            "strata_observed": strata_observed,
            "sample_type": panel.sample_type,
            "methodology": "matched_jevons_fixed_base_laspeyres",
        })

    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(output_rows[0].keys()))
        writer.writeheader()
        writer.writerows(output_rows)

    print(f"[APIx Back-Test] Exported {len(output_rows)} daily index points to: {output_csv}")

    # --- Report -----------------------------------------------------------
    min_val = min(aggregate_series)
    max_val = max(aggregate_series)
    final_val = aggregate_series[-1]
    cumulative_return = round(((final_val - 100.0) / 100.0) * 100, 2)

    _write_report(
        output_report, panel, calendar, series_len, output_rows,
        final_val, min_val, max_val, cumulative_return,
        len(elementary_indices), strata_total, strata_observed, mean_coverage,
    )
    print(f"[APIx Back-Test] Wrote report to: {output_report}")

    return {
        "series_length": series_len,
        "base_value": 100.0,
        "final_value": final_val,
        "min_value": min_val,
        "max_value": max_val,
        "cumulative_change_pct": cumulative_return,
        "output_csv": str(output_csv),
        "sample_type": panel.sample_type,
        "is_synthetic": panel.is_synthetic,
        "strata_observed": strata_observed,
        "strata_total": strata_total,
    }


def _write_report(
    path, panel, calendar, series_len, output_rows,
    final_val, min_val, max_val, cumulative_return,
    n_elementary, strata_total, strata_observed, mean_coverage,
) -> None:
    """Render the markdown report, with provenance stated up front."""
    if panel.is_synthetic:
        banner = (
            "> [!WARNING]\n"
            "> **This run used a SYNTHETIC stand-in panel, not real airfare data.**\n"
            "> The real Kaggle EaseMyTrip panel was not present on disk, so\n"
            "> `scripts/run_kaggle_backtest.py` generated a reproducible stand-in.\n"
            "> The numbers below verify that the index PIPELINE is arithmetically\n"
            "> sound. They are **not** evidence about real Indian airfare movement\n"
            "> and must not be presented as such.\n"
            ">\n"
            "> To produce a real-data back-test, download `Clean_Dataset.csv` into\n"
            "> `data/raw/` (see `docs/KAGGLE_EASEMYTRIP_DATASET.md`) and re-run.\n"
        )
        title_suffix = " (SYNTHETIC STAND-IN)"
        observation_word = "synthetic panel observations"
    else:
        banner = ""
        title_suffix = ""
        observation_word = "real-world domestic airline price observations"

    content = f"""# APIx 50-Day Historical Panel Back-Test Report{title_suffix}

{banner}
**Dataset**: {panel.label}
**Source file**: `{panel.path.name}`
**Sample type**: `{panel.sample_type}`
**Sample period**: {series_len} days ({calendar[0].isoformat()} to {calendar[-1].isoformat()})
**Coverage**: {output_rows[0]['routes_quoted']} trunk routes · {output_rows[0]['advance_windows']} advance horizons (T+1, T+7, T+15, T+30, T+45)
**Aggregation**: Matched-sample Jevons elementary indices aggregated via a
DGCA passenger-traffic weighted **fixed-base Laspeyres**

---

## 1. Executive Summary

This back-test evaluates the arithmetic stability and advance-horizon
behaviour of the APIx index system over **{series_len} consecutive days** of
{observation_word}.

| Metric | Result |
|---|---|
| Base value (day 0) | 100.000 |
| Final value (day {series_len - 1}) | {final_val:.3f} |
| Cumulative movement | {cumulative_return:+.2f}% |
| Min index value | {min_val:.3f} |
| Max index value | {max_val:.3f} |
| Elementary strata computed | {n_elementary} of {strata_total} |
| Strata with observations | {strata_observed} of {strata_total} |
| Mean daily stratum coverage | {mean_coverage:.1f}% |

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
"""
    for r in output_rows[:5]:
        content += f"| {r['day']} | {r['date']} | {r['aggregate_index_value']:.3f} | {r['change_pct']:+.2f}% |\n"
    content += "| ... | ... | ... | ... |\n"
    for r in output_rows[-5:]:
        content += f"| {r['day']} | {r['date']} | {r['aggregate_index_value']:.3f} | {r['change_pct']:+.2f}% |\n"

    content += f"""
---

## 4. Reproducibility & Audit Trail

- Series artifact: `apix/data/{OUTPUT_SERIES_CSV.name}`
- Every row carries `sample_type={panel.sample_type}`.
- Automated tests: `tests/test_kaggle_backtest.py`, `tests/test_index.py`
- The stand-in generator is seeded with SHA-256, not Python's per-process
  salted `hash()`, so repeated runs reproduce the panel byte for byte.
"""

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the 50-day APIx back-test over a historical flight price panel."
    )
    parser.add_argument("--dataset", type=Path, default=None, help="Path to Clean_Dataset.csv")
    parser.add_argument("--output", type=Path, default=OUTPUT_SERIES_CSV, help="Output path for series CSV")
    parser.add_argument("--report", type=Path, default=OUTPUT_REPORT_MD, help="Output path for the markdown report")
    args = parser.parse_args()

    results = run_kaggle_backtest(
        dataset_path=args.dataset,
        output_csv=args.output,
        output_report=args.report,
    )
    provenance = "SYNTHETIC" if results["is_synthetic"] else "REAL"
    print(
        f"\n[APIx Back-Test Complete] {provenance} | Series: {results['series_length']} days | "
        f"Final Index: {results['final_value']:.2f} ({results['cumulative_change_pct']:+.2f}%)"
    )


if __name__ == "__main__":
    main()

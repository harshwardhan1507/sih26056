#!/usr/bin/env python3
"""
Derive DGCA passenger route weights for the APIx 12-route basket.

Ingests DGCA monthly domestic city-pair traffic from `aggregated/domestic/city.csv`
(sourced from Vonter/india-aviation-traffic under ODbL-1.0), filters to the trailing
12-month period (June 2025 – May 2026), performs bidirectional aggregation and
multi-airport consolidation (Goa & Mumbai), and normalizes route shares to sum to 1.0.

Outputs to `apix/data/route_weights.json` (and optionally YAML/CSV).
See `docs/data-sources/dgca-route-weights.md` for methodology and legal basis.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import sys
import urllib.request
from datetime import date
from io import StringIO
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

# Pinned upstream commit for reproducible provenance
UPSTREAM_COMMIT = "42deff14ffaa81f8596353ec2744ccef4d04e7df"
UPSTREAM_RAW_URL = (
    f"https://raw.githubusercontent.com/Vonter/india-aviation-traffic/"
    f"{UPSTREAM_COMMIT}/aggregated/domestic/city.csv"
)

# Standard 12 APIx routes in canonical direction (matches BASKET_ROUTES in apix/index/weights.py)
BASKET_ROUTES: tuple[str, ...] = (
    "DEL-BOM", "DEL-BLR", "DEL-CCU", "DEL-MAA", "DEL-HYD",
    "BOM-BLR", "BOM-MAA", "BOM-CCU",
    "BLR-HYD", "BLR-MAA",
    "DEL-GOI", "BOM-GOI",
)

# Canonical city to IATA code mapping (case-insensitive)
# Implements Metropolitan Catchment Aggregation per docs/data-sources/dgca-route-weights.md §3.3
CITY_TO_IATA: Dict[str, str] = {
    # Delhi
    "DELHI": "DEL",
    "NEW DELHI": "DEL",
    # Mumbai & Navi Mumbai
    "MUMBAI": "BOM",
    "MUMBAI (MUMBAI)": "BOM",
    "MUMBAI (NAVI MUMBAI)": "BOM",
    # Bengaluru
    "BENGALURU": "BLR",
    "BANGALORE": "BLR",
    # Kolkata
    "KOLKATA": "CCU",
    "CALCUTTA": "CCU",
    # Chennai
    "CHENNAI": "MAA",
    "MADRAS": "MAA",
    # Hyderabad
    "HYDERABAD": "HYD",
    # Goa Metropolitan Catchment (Dabolim GOI + Mopa GOX across all historical naming phases)
    "GOA": "GOI",
    "DABOLIM": "GOI",
    "MOPA, GOA": "GOI",
    "MOPA": "GOI",
    "GOA (DABOLIM, SOUTH GOA)": "GOI",
    "GOA (MOPA, NORTH GOA)": "GOI",
}


def map_city_to_iata(city_name: str) -> Optional[str]:
    """Map raw DGCA city name string to canonical IATA code, or None if unmapped."""
    cleaned = city_name.strip().upper()
    return CITY_TO_IATA.get(cleaned)


def canonicalize_route(origin: str, destination: str) -> Optional[str]:
    """
    Given two raw city names, map to IATA codes and check if the pair
    (in either direction) belongs to the 12-route basket.
    Returns canonical route string (e.g. 'DEL-BOM') or None.
    """
    c1 = map_city_to_iata(origin)
    c2 = map_city_to_iata(destination)
    if not c1 or not c2 or c1 == c2:
        return None

    pair_forward = f"{c1}-{c2}"
    if pair_forward in BASKET_ROUTES:
        return pair_forward

    pair_reverse = f"{c2}-{c1}"
    if pair_reverse in BASKET_ROUTES:
        return pair_reverse

    return None


def is_in_period(year: int, month: int, start_period: str, end_period: str) -> bool:
    """Check if (year, month) falls within [start_period, end_period] inclusive (YYYY-MM)."""
    period_str = f"{year:04d}-{month:02d}"
    return start_period <= period_str <= end_period


def derive_weights_from_reader(
    reader: csv.DictReader,
    start_period: str = "2025-06",
    end_period: str = "2026-05",
    basket_routes: Sequence[str] = BASKET_ROUTES,
) -> Tuple[Dict[str, float], Dict[str, int], int, int]:
    """
    Process CSV rows and compute normalized route weights over the specified period.

    Returns:
        (weights, route_pax, total_basket_pax, all_domestic_pax)
    """
    route_pax: Dict[str, int] = {r: 0 for r in basket_routes}
    all_domestic_pax = 0

    for row in reader:
        try:
            year = int(row["Year"])
            month = int(row["Month"])
        except (KeyError, ValueError):
            continue

        if not is_in_period(year, month, start_period, end_period):
            continue

        try:
            pax_to = int(float(row.get("PaxToCity2", 0) or 0))
            pax_from = int(float(row.get("PaxFromCity2", 0) or 0))
        except (ValueError, TypeError):
            continue

        pair_pax = pax_to + pax_from
        all_domestic_pax += pair_pax

        c_route = canonicalize_route(row.get("City1", ""), row.get("City2", ""))
        if c_route and c_route in route_pax:
            route_pax[c_route] += pair_pax

    total_basket_pax = sum(route_pax.values())
    if total_basket_pax == 0:
        raise ValueError(
            f"Zero passenger traffic found for basket routes in window {start_period} to {end_period}."
        )

    # Compute shares rounded to 6 decimal places
    raw_weights: Dict[str, float] = {
        r: round(route_pax[r] / total_basket_pax, 6)
        for r in basket_routes
    }

    # Normalize slight rounding differences so sum is exactly 1.0
    weight_sum = sum(raw_weights.values())
    diff = round(1.0 - weight_sum, 6)
    if diff != 0.0:
        # Adjust largest route (typically DEL-BOM) to absorb rounding residual
        largest_route = max(raw_weights, key=raw_weights.get)
        raw_weights[largest_route] = round(raw_weights[largest_route] + diff, 6)

    return raw_weights, route_pax, total_basket_pax, all_domestic_pax


def build_weight_payload(
    weights: Dict[str, float],
    route_pax: Dict[str, int],
    total_basket_pax: int,
    coverage_month: str = "2026-05",
    t12m_start: str = "2025-06",
    t12m_end: str = "2026-05",
) -> Dict:
    """Build canonical JSON payload matching apix/data/route_weights.json schema."""
    sorted_weights = dict(sorted(weights.items(), key=lambda item: item[1], reverse=True))

    return {
        "_comment": "Route weights derived from DGCA domestic city-pair passenger traffic data.",
        "source": "Vonter/india-aviation-traffic (https://github.com/Vonter/india-aviation-traffic), licensed ODbL-1.0. Data sourced from DGCA.",
        "coverage_month": coverage_month,
        "generated_date": date.today().isoformat(),
        "methodology": (
            f"Passenger shares computed over the Trailing 12-Month window {t12m_start} to {t12m_end} "
            f"from aggregated/domestic/city.csv. PaxToCity2 + PaxFromCity2 summed across all months "
            f"for each city pair, then restricted to the 12-route APIx basket and normalised to sum to 1.0. "
            f"City names mapped to IATA codes with Metropolitan Catchment Aggregation: "
            f"DELHI=DEL, MUMBAI/MUMBAI(MUMBAI)/MUMBAI(NAVI MUMBAI)=BOM, BENGALURU=BLR, KOLKATA=CCU, "
            f"CHENNAI=MAA, HYDERABAD=HYD, GOA/GOA(DABOLIM,SOUTH GOA)/GOA(MOPA,NORTH GOA)/MOPA,GOA/DABOLIM=GOI."
        ),
        "total_basket_pax": total_basket_pax,
        "weights": sorted_weights,
    }


def find_default_csv_path() -> Optional[Path]:
    """Search common local candidate paths for aggregated/domestic/city.csv."""
    candidates = [
        Path("data/raw/dgca/aggregated/domestic/city.csv"),
        Path("data/raw/aggregated/domestic/city.csv"),
        Path("aggregated/domestic/city.csv"),
        Path("data/city.csv"),
        Path("city.csv"),
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def fetch_csv_from_github() -> str:
    """Fetch raw CSV from pinned GitHub repository commit."""
    print(f"Downloading DGCA city traffic CSV from {UPSTREAM_RAW_URL} ...")
    req = urllib.request.Request(
        UPSTREAM_RAW_URL,
        headers={"User-Agent": "APIx-Weight-Derivation/1.0"},
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return response.read().decode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Derive DGCA passenger route weights for the APIx 12-route basket."
    )
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        default=None,
        help="Path to local aggregated/domestic/city.csv. Auto-detected if omitted.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path(__file__).resolve().parent.parent / "apix" / "data" / "route_weights.json",
        help="Path to output JSON file (default: apix/data/route_weights.json).",
    )
    parser.add_argument(
        "--download",
        action="store_true",
        help=f"Download CSV directly from GitHub commit {UPSTREAM_COMMIT[:7]}.",
    )
    parser.add_argument(
        "--start-period",
        default="2025-06",
        help="Start of T12M period in YYYY-MM (default: 2025-06).",
    )
    parser.add_argument(
        "--end-period",
        default="2026-05",
        help="End of T12M period in YYYY-MM (default: 2026-05).",
    )
    args = parser.parse_args()

    csv_content: Optional[str] = None
    csv_path: Optional[Path] = None

    if args.download:
        csv_content = fetch_csv_from_github()
    elif args.input:
        csv_path = args.input
        if not csv_path.is_file():
            print(f"Error: Specified input file not found: {csv_path}", file=sys.stderr)
            return 1
    else:
        csv_path = find_default_csv_path()
        if not csv_path:
            print(
                "Local aggregated/domestic/city.csv not found in candidate paths.\n"
                "Use --input <path> to specify, or --download to fetch from GitHub.",
                file=sys.stderr,
            )
            return 1

    if csv_content is not None:
        reader = csv.DictReader(StringIO(csv_content))
    else:
        print(f"Reading local DGCA CSV from: {csv_path}")
        f = open(csv_path, "r", encoding="utf-8", newline="")
        reader = csv.DictReader(f)

    weights, route_pax, total_basket_pax, all_domestic_pax = derive_weights_from_reader(
        reader,
        start_period=args.start_period,
        end_period=args.end_period,
    )

    if csv_path is not None and "f" in locals():
        f.close()

    payload = build_weight_payload(
        weights=weights,
        route_pax=route_pax,
        total_basket_pax=total_basket_pax,
        coverage_month=args.end_period,
        t12m_start=args.start_period,
        t12m_end=args.end_period,
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as out_f:
        json.dump(payload, out_f, indent=2)

    coverage_pct = (total_basket_pax / all_domestic_pax * 100) if all_domestic_pax > 0 else 0.0
    print(f"\nSuccessfully derived weights across {len(weights)} basket routes:")
    for r, w in payload["weights"].items():
        print(f"  {r:8s}: {w:.6f} ({route_pax[r]:,d} pax)")
    print(f"\nTotal Basket Passenger Traffic: {total_basket_pax:,d}")
    if all_domestic_pax > 0:
        print(f"Total All-India Domestic Traffic: {all_domestic_pax:,d} (Basket Coverage: {coverage_pct:.2f}%)")
    print(f"Weights sum to: {sum(weights.values()):.6f}")
    print(f"Wrote route weights to: {args.output}")

    return 0


if __name__ == "__main__":
    sys.exit(main())

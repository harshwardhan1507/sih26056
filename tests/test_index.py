"""
Unit tests for Jevons elementary index and chained Laspeyres upper-level aggregation.
"""

import math
import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from apix.index.elementary import jevons_ratio, build_elementary_index
from apix.index.aggregate import build_aggregate_index
from apix.index.weights import load_weights, BASKET_ROUTES, DEFAULT_WEIGHT_FILE


def test_jevons_ratio_single_carrier():
    yesterday = {"6E": 4000.0}
    today = {"6E": 5000.0}
    ratio = jevons_ratio(today, yesterday)
    assert ratio is not None
    assert math.isclose(ratio, 1.25, rel_tol=1e-6)


def test_jevons_ratio_multiple_carriers():
    yesterday = {"6E": 1000.0, "AI": 2000.0}
    today = {"6E": 2000.0, "AI": 8000.0}
    # Relatives: 6E = 2.0, AI = 4.0
    # Geometric mean: sqrt(2.0 * 4.0) = sqrt(8.0)
    expected = math.sqrt(8.0)
    ratio = jevons_ratio(today, yesterday)
    assert ratio is not None
    assert math.isclose(ratio, expected, rel_tol=1e-6)


def test_jevons_ratio_matched_sample_drops_unmatched():
    # Carrier SG is missing yesterday; carrier QP is sold out today (None or missing)
    yesterday = {"6E": 5000.0, "AI": 6000.0, "QP": 4500.0}
    today = {"6E": 5500.0, "AI": 6600.0, "SG": 4800.0, "QP": None}

    # Only 6E (5500/5000 = 1.1) and AI (6600/6000 = 1.1) are matched
    expected = 1.1
    ratio = jevons_ratio(today, yesterday)
    assert ratio is not None
    assert math.isclose(ratio, expected, rel_tol=1e-6)


def test_jevons_ratio_no_overlap():
    yesterday = {"6E": 5000.0}
    today = {"AI": 6000.0}
    assert jevons_ratio(today, yesterday) is None


def test_build_elementary_index_constant_prices():
    prices = [{"6E": 5000.0, "AI": 5500.0} for _ in range(5)]
    index = build_elementary_index(prices, base_value=100.0)
    assert len(index) == 5
    assert all(math.isclose(val, 100.0, rel_tol=1e-6) for val in index)


def test_build_elementary_index_chained():
    # Day 0 -> Day 1: +10%
    # Day 1 -> Day 2: -10%
    prices = [
        {"6E": 1000.0},
        {"6E": 1100.0},
        {"6E": 990.0},
    ]
    index = build_elementary_index(prices, base_value=100.0)
    assert math.isclose(index[0], 100.0, rel_tol=1e-6)
    assert math.isclose(index[1], 110.0, rel_tol=1e-6)
    assert math.isclose(index[2], 99.0, rel_tol=1e-6)


def test_build_aggregate_index():
    # Two elementary series
    series_a = [100.0, 110.0, 121.0]  # +10% each day
    series_b = [100.0, 100.0, 100.0]  # flat
    weights = {"A": 0.6, "B": 0.4}

    elementary = {"A": series_a, "B": series_b}
    agg = build_aggregate_index(elementary, weights)

    assert len(agg) == 3
    assert math.isclose(agg[0], 100.0, rel_tol=1e-6)

    # Day 1 relative: 0.6 * (110/100) + 0.4 * (100/100) = 0.66 + 0.40 = 1.06
    assert math.isclose(agg[1], 106.0, rel_tol=1e-6)

    # Day 2 relative: 0.6 * (121/110) + 0.4 * (100/100) = 0.6 * 1.1 + 0.4 = 1.06
    assert math.isclose(agg[2], 106.0 * 1.06, rel_tol=1e-6)


# ---------------------------------------------------------------------------
# Weight file tests (issue #10 acceptance criteria)
# ---------------------------------------------------------------------------

def test_weights_sum_to_one():
    """Weights in route_weights.json must sum to 1.0 (±1e-4)."""
    weights = load_weights(DEFAULT_WEIGHT_FILE)
    total = sum(weights.values())
    assert math.isclose(total, 1.0, abs_tol=1e-4), (
        f"Weights sum to {total:.8f}, expected 1.0"
    )


def test_weights_required_routes_present():
    """All 12 basket routes must be present in route_weights.json."""
    weights = load_weights(DEFAULT_WEIGHT_FILE)
    missing = [r for r in BASKET_ROUTES if r not in weights]
    assert not missing, f"Missing routes in weight file: {missing}"


if __name__ == "__main__":
    test_jevons_ratio_single_carrier()
    test_jevons_ratio_multiple_carriers()
    test_jevons_ratio_matched_sample_drops_unmatched()
    test_jevons_ratio_no_overlap()
    test_build_elementary_index_constant_prices()
    test_build_elementary_index_chained()
    test_build_aggregate_index()
    test_weights_sum_to_one()
    test_weights_required_routes_present()
    print("All unit tests passed successfully!")

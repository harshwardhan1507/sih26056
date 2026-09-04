"""
Unit tests for Jevons elementary index and Laspeyres upper-level aggregation.
"""

import math
import random
import sys
from pathlib import Path

import pytest

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from apix.index.elementary import jevons_ratio, build_elementary_index
from apix.index.aggregate import (
    CHAINED,
    FIXED_BASE,
    GEOMETRIC,
    build_aggregate_index,
)
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
    """Fixed-base Laspeyres: every day is compared to day 0, not to day t-1."""
    series_a = [100.0, 110.0, 121.0]  # +10% each day
    series_b = [100.0, 100.0, 100.0]  # flat
    weights = {"A": 0.6, "B": 0.4}

    elementary = {"A": series_a, "B": series_b}
    agg = build_aggregate_index(elementary, weights)

    assert len(agg) == 3
    assert math.isclose(agg[0], 100.0, rel_tol=1e-6)

    # Day 1 vs base: 0.6 * (110/100) + 0.4 * (100/100) = 0.66 + 0.40 = 1.06
    assert math.isclose(agg[1], 106.0, rel_tol=1e-6)

    # Day 2 vs base: 0.6 * (121/100) + 0.4 * (100/100) = 0.726 + 0.40 = 1.126
    assert math.isclose(agg[2], 112.6, rel_tol=1e-6)


def test_build_aggregate_index_chained_method():
    """The legacy daily-chained method is still available for drift diagnostics."""
    elementary = {"A": [100.0, 110.0, 121.0], "B": [100.0, 100.0, 100.0]}
    weights = {"A": 0.6, "B": 0.4}
    agg = build_aggregate_index(elementary, weights, method=CHAINED)

    # Day 1 link: 0.6 * 1.10 + 0.4 = 1.06
    assert math.isclose(agg[1], 106.0, rel_tol=1e-6)
    # Day 2 link: 0.6 * (121/110) + 0.4 = 1.06, applied to the previous level
    assert math.isclose(agg[2], 106.0 * 1.06, rel_tol=1e-6)


# ---------------------------------------------------------------------------
# Chain-drift regression tests
#
# These guard the defect that made the published 45-day series read +29.27%
# while the underlying fare level had moved +0.94%. A daily-chained weighted
# ARITHMETIC mean of relatives is upward biased by exp(sigma^2) per link
# (Jensen), so noise alone compounds into fake inflation. The headline method
# must be immune to this.
# ---------------------------------------------------------------------------

def _flat_price_panel(n_series=40, n_days=45, n_carriers=5, sigma=0.08, seed=7):
    """
    Elementary indices built from prices whose TRUE level never moves:
    every observation is base * iid lognormal noise. A correct aggregate
    index must therefore stay at ~100 for the whole window.
    """
    rng = random.Random(seed)
    return {
        f"R{r}": build_elementary_index([
            {f"C{c}": 5000.0 * math.exp(rng.gauss(0, sigma)) for c in range(n_carriers)}
            for _ in range(n_days)
        ])
        for r in range(n_series)
    }


def test_no_chain_drift_on_trendless_prices():
    """Headline (fixed-base) index must not drift when prices are trendless."""
    elementary = _flat_price_panel()
    weights = {k: 1.0 / len(elementary) for k in elementary}

    agg = build_aggregate_index(elementary, weights)

    assert abs(agg[-1] - 100.0) < 1.0, (
        f"Fixed-base index drifted to {agg[-1]:.3f} on flat prices; "
        "expected to stay within 1 point of 100."
    )


def test_no_chain_drift_geometric_method():
    """The geometric chained alternative must also be drift-free."""
    elementary = _flat_price_panel()
    weights = {k: 1.0 / len(elementary) for k in elementary}

    agg = build_aggregate_index(elementary, weights, method=GEOMETRIC)

    assert abs(agg[-1] - 100.0) < 1.0, (
        f"Geometric index drifted to {agg[-1]:.3f} on flat prices."
    )


def test_chained_method_exhibits_known_drift():
    """
    Pins the defect itself: the daily-chained arithmetic method DOES drift
    upward on the same trendless data. If this ever stops being true the
    drift documentation is stale and should be revisited.
    """
    elementary = _flat_price_panel()
    weights = {k: 1.0 / len(elementary) for k in elementary}

    fixed = build_aggregate_index(elementary, weights, method=FIXED_BASE)
    chained = build_aggregate_index(elementary, weights, method=CHAINED)

    assert chained[-1] > fixed[-1] + 2.0, (
        "Expected the daily-chained method to drift measurably above the "
        f"fixed-base method; got chained={chained[-1]:.3f} fixed={fixed[-1]:.3f}."
    )


def test_index_returns_to_base_when_prices_return_to_base():
    """
    Transitivity check a statistical office would run: if prices go up and
    then come back to exactly where they started, the index must return to
    100. The daily chain fails this; the headline method must not.
    """
    up_down = [100.0, 130.0, 90.0, 115.0, 100.0]
    elementary = {"A": list(up_down), "B": list(up_down)}
    weights = {"A": 0.5, "B": 0.5}

    agg = build_aggregate_index(elementary, weights)

    assert math.isclose(agg[-1], 100.0, rel_tol=1e-9), (
        f"Prices returned to base but index reads {agg[-1]:.6f}."
    )


def test_rebase_period_relinks_without_daily_drift():
    """Re-linking every N days must stay far closer to truth than daily chaining."""
    elementary = _flat_price_panel()
    weights = {k: 1.0 / len(elementary) for k in elementary}

    rebased = build_aggregate_index(elementary, weights, rebase_period_days=30)
    chained = build_aggregate_index(elementary, weights, method=CHAINED)

    assert abs(rebased[-1] - 100.0) < abs(chained[-1] - 100.0)
    assert abs(rebased[-1] - 100.0) < 2.0


# ---------------------------------------------------------------------------
# Aggregation input validation — these used to fail silently or crash obscurely
# ---------------------------------------------------------------------------

def test_aggregate_rejects_empty_input():
    with pytest.raises(ValueError, match="empty"):
        build_aggregate_index({}, {})


def test_aggregate_rejects_ragged_series():
    with pytest.raises(ValueError, match="same length"):
        build_aggregate_index({"A": [100.0] * 5, "B": [100.0] * 3}, {"A": 0.5, "B": 0.5})


def test_aggregate_rejects_missing_weight():
    """A weight-key mismatch used to silently collapse the index to 0.0."""
    with pytest.raises(KeyError):
        build_aggregate_index({"DEL-BOM|30": [100.0, 101.0]}, {"DEL-BOM": 1.0})


def test_aggregate_rejects_zero_total_weight():
    with pytest.raises(ValueError, match="sum to"):
        build_aggregate_index({"A": [100.0, 101.0]}, {"A": 0.0})


def test_aggregate_rejects_unknown_method():
    with pytest.raises(ValueError, match="Unknown method"):
        build_aggregate_index({"A": [100.0, 101.0]}, {"A": 1.0}, method="carli")


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
    test_build_aggregate_index_chained_method()
    test_no_chain_drift_on_trendless_prices()
    test_no_chain_drift_geometric_method()
    test_chained_method_exhibits_known_drift()
    test_index_returns_to_base_when_prices_return_to_base()
    test_rebase_period_relinks_without_daily_drift()
    test_weights_sum_to_one()
    test_weights_required_routes_present()
    print("All unit tests passed successfully!")

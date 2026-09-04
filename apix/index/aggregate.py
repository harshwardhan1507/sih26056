"""
Upper-level aggregation of elementary indices into the headline APIx series.

Method (why it is NOT a daily chain)
------------------------------------
A Laspeyres index aggregates price relatives with fixed expenditure weights.
There are two ways to run it over a long daily series, and they are NOT
equivalent:

  Fixed base   I_t = 100 * SUM_i w_i * (I_i,t / I_i,base)
  Daily chain  I_t = I_{t-1} * SUM_i w_i * (I_i,t / I_i,t-1)

The daily chain suffers **chain drift**. The weighted ARITHMETIC mean of
price relatives is upward biased by Jensen's inequality: for relatives that
are noisy but trendless, E[SUM w_i r_i] = exp(sigma^2) > 1 per link. Over
n links the bias compounds to exp(n * sigma^2). With airfare-scale daily
dispersion (sigma ~ 0.08) that is roughly +0.64% PER DAY of purely spurious
inflation -- about +30% over a 45-day window on prices that never moved.

This is the well-documented high-frequency chain-drift problem
(Ivancic, Diewert & Fox 2011; Eurostat 2022 "Guide on Multilateral Methods";
ONS 2023 alternative data methodology). National statistical offices do not
daily-chain. Neither does CPI: it is a fixed-base Laspeyres within a
weight-reference period, re-linked at long intervals.

APIx therefore defaults to ``method="fixed_base"``. ``rebase_period_days``
re-links at a chosen interval (e.g. 30) so the basket can be refreshed
without inheriting daily drift. ``method="chained"`` is retained ONLY so the
drift can be demonstrated side by side -- it must not be used to publish.
``method="geometric"`` is a drift-resistant chained alternative (weighted
geometric mean of relatives) for sensitivity analysis.

See docs/METHODOLOGY_CHAIN_DRIFT.md and tests/test_index.py::test_no_chain_drift.
"""

from __future__ import annotations

import math
from typing import Optional

# Aggregation methods accepted by build_aggregate_index().
FIXED_BASE = "fixed_base"
CHAINED = "chained"
GEOMETRIC = "geometric"
_METHODS = (FIXED_BASE, CHAINED, GEOMETRIC)

BASE_VALUE = 100.0


def _validate(
    elementary_indices: dict[str, list[float]],
    weights: dict[str, float],
) -> tuple[list[str], int, dict[str, float]]:
    """
    Validate inputs and return (keys, n_days, normalised_weights).

    Fails loudly rather than silently producing a wrong index. The previous
    implementation returned a series of 0.0 when no weight key matched an
    elementary key -- a catastrophic result that looked like data.
    """
    if not elementary_indices:
        raise ValueError("elementary_indices is empty; nothing to aggregate.")

    keys = list(elementary_indices.keys())

    lengths = {k: len(elementary_indices[k]) for k in keys}
    n_days = len(elementary_indices[keys[0]])
    ragged = {k: n for k, n in lengths.items() if n != n_days}
    if ragged:
        raise ValueError(
            f"Elementary series must all be the same length; got {n_days} for "
            f"'{keys[0]}' but {ragged} for others. Align the series to a common "
            "calendar before aggregating."
        )
    if n_days == 0:
        raise ValueError("Elementary series are empty (zero days).")

    missing = [k for k in keys if k not in weights]
    if missing:
        raise KeyError(
            f"No weight supplied for elementary series {missing}. Weight keys "
            "must match elementary keys exactly (e.g. 'DEL-BOM|30'). Check "
            "that route-level weights were expanded across advance windows."
        )

    total_weight = sum(weights[k] for k in keys)
    if total_weight <= 0:
        raise ValueError(
            f"Weights over the supplied elementary keys sum to {total_weight}; "
            "expected a positive total."
        )

    normalised = {k: weights[k] / total_weight for k in keys}
    return keys, n_days, normalised


def build_aggregate_index(
    elementary_indices: dict[str, list[float]],
    weights: dict[str, float],
    *,
    method: str = FIXED_BASE,
    rebase_period_days: Optional[int] = None,
    base_value: float = BASE_VALUE,
) -> list[float]:
    """
    Aggregate per-(route, advance_window) elementary indices into the APIx series.

    Parameters
    ----------
    elementary_indices:
        ``{"DEL-BOM|30": [100.0, 100.4, ...], ...}`` -- equal-length series.
    weights:
        ``{"DEL-BOM|30": 0.036, ...}`` -- one entry per elementary key.
        Re-normalised internally, so any positive scale is accepted.
    method:
        ``"fixed_base"`` (default, drift-free), ``"geometric"``
        (drift-resistant chained), or ``"chained"`` (daily-chained Laspeyres,
        DRIFTS UPWARD -- diagnostic use only).
    rebase_period_days:
        Re-link the fixed-base computation every N days, so weights can be
        refreshed without daily chaining. ``None`` = single fixed base.
        Ignored for the non-fixed-base methods.
    base_value:
        Index level at day 0 (default 100.0).

    Returns
    -------
    list[float]
        The aggregate index series, same length as the elementary series.

    Raises
    ------
    ValueError
        Empty input, ragged series lengths, non-positive weight total, or an
        unknown ``method``.
    KeyError
        An elementary key has no corresponding weight.
    """
    if method not in _METHODS:
        raise ValueError(f"Unknown method {method!r}; expected one of {_METHODS}.")

    keys, n_days, w = _validate(elementary_indices, weights)

    if method == CHAINED:
        return _build_chained(elementary_indices, keys, w, n_days, base_value)
    if method == GEOMETRIC:
        return _build_geometric(elementary_indices, keys, w, n_days, base_value)
    return _build_fixed_base(
        elementary_indices, keys, w, n_days, base_value, rebase_period_days
    )


def _build_fixed_base(
    elementary_indices: dict[str, list[float]],
    keys: list[str],
    w: dict[str, float],
    n_days: int,
    base_value: float,
    rebase_period_days: Optional[int],
) -> list[float]:
    """
    Direct Laspeyres against a fixed base period, optionally re-linked.

    Because every day is compared to the SAME base, noise does not compound:
    a day whose prices match the base returns exactly to base_value.
    """
    if rebase_period_days is not None and rebase_period_days < 1:
        raise ValueError("rebase_period_days must be >= 1 when supplied.")

    aggregate = [base_value]
    link_start = 0                 # index of the current link's base period
    link_level = base_value        # accumulated level at link_start

    for t in range(1, n_days):
        if rebase_period_days is not None and (t - link_start) >= rebase_period_days:
            link_level = aggregate[t - 1]
            link_start = t - 1

        weighted_relative = 0.0
        for k in keys:
            series = elementary_indices[k]
            base_price = series[link_start]
            # A zero/absent base leaves that stratum unable to contribute a
            # relative; treat it as no change rather than dividing by zero.
            relative = series[t] / base_price if base_price else 1.0
            weighted_relative += w[k] * relative

        aggregate.append(link_level * weighted_relative)

    return aggregate


def _build_geometric(
    elementary_indices: dict[str, list[float]],
    keys: list[str],
    w: dict[str, float],
    n_days: int,
    base_value: float,
) -> list[float]:
    """
    Chained weighted GEOMETRIC mean of relatives.

    Retains day-over-day chaining but is unbiased for lognormal noise, so it
    does not exhibit the arithmetic chain's exp(sigma^2)-per-link drift.
    Useful as a sensitivity check against the fixed-base headline.
    """
    aggregate = [base_value]
    for t in range(1, n_days):
        log_sum = 0.0
        for k in keys:
            series = elementary_indices[k]
            prev = series[t - 1]
            relative = series[t] / prev if prev else 1.0
            if relative <= 0:
                relative = 1.0
            log_sum += w[k] * math.log(relative)
        aggregate.append(aggregate[-1] * math.exp(log_sum))
    return aggregate


def _build_chained(
    elementary_indices: dict[str, list[float]],
    keys: list[str],
    w: dict[str, float],
    n_days: int,
    base_value: float,
) -> list[float]:
    """
    Daily-chained Laspeyres. DRIFTS UPWARD on noisy trendless prices.

    Kept only so the drift can be quantified against the fixed-base headline
    (see tests/test_index.py::test_chained_method_exhibits_known_drift).
    Do not publish this series.
    """
    aggregate = [base_value]
    for t in range(1, n_days):
        weighted_relative = 0.0
        for k in keys:
            series = elementary_indices[k]
            prev = series[t - 1]
            relative = series[t] / prev if prev else 1.0
            weighted_relative += w[k] * relative
        aggregate.append(aggregate[-1] * weighted_relative)
    return aggregate

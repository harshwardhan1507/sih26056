"""
Statistical outlier detection for volatile airfare prices.

Adheres to national statistical institute methodology for alternative data
(Handbook §4.4 citing NIESR / Eurostat HICP standards):
  - Airfares follow right-skewed lognormal distributions.
  - Price distributions are evaluated on log-transformed fares: y = ln(price).
  - Implements two robust non-parametric detection methods:
      1. Tukey's Log-IQR Fence: [Q1 - k * IQR, Q3 + k * IQR]
      2. Median Absolute Deviation (MAD): z = 0.6745 * |y - M| / MAD

Handles critical numerical and statistical edge cases:
  - Small sample size (N < 4): Bypasses detection to avoid false positives on oligopoly routes.
  - Zero dispersion (IQR = 0 or MAD = 0): Protects against division by zero; flags 0 outliers.
  - Sold-out flights (price is None): Skipped in statistical fences, preserves 'sold_out' flag.
  - Never deletes rows: Outliers are tagged with quality_flag='outlier' for auditable downstream handling.
"""

from __future__ import annotations

import math
from dataclasses import replace
from datetime import date
from typing import Dict, List, Optional, Sequence, Set, Tuple

from apix.collector.adapters.base import FareQuote


def compute_percentile(sorted_data: Sequence[float], percentile: float) -> float:
    """
    Compute empirical percentile using linear interpolation between closest ranks.
    percentile: float between 0.0 and 1.0 (e.g. 0.25 for Q1, 0.75 for Q3).
    """
    n = len(sorted_data)
    if n == 0:
        raise ValueError("Cannot compute percentile of empty sequence")
    if n == 1:
        return sorted_data[0]

    rank = percentile * (n - 1)
    low_idx = int(math.floor(rank))
    high_idx = int(math.ceil(rank))
    weight = rank - low_idx

    return (1.0 - weight) * sorted_data[low_idx] + weight * sorted_data[high_idx]


def compute_median(sorted_data: Sequence[float]) -> float:
    """Compute median of a sorted float sequence."""
    n = len(sorted_data)
    if n == 0:
        raise ValueError("Cannot compute median of empty sequence")
    mid = n // 2
    if n % 2 != 0:
        return sorted_data[mid]
    return (sorted_data[mid - 1] + sorted_data[mid]) / 2.0


def identify_outlier_indices_tukey(
    prices: Sequence[float],
    k: float = 2.0,
    min_sample_size: int = 4,
) -> Set[int]:
    """
    Identify outlier indices using Tukey's fence on natural log prices.

    Args:
        prices: List of positive float prices.
        k: Fence multiplier (1.5 = mild, 2.0 = standard, 3.0 = extreme).
        min_sample_size: Minimum sample size required to apply fences.

    Returns:
        Set of indices in `prices` that are flagged as outliers.
    """
    n = len(prices)
    if n < min_sample_size:
        return set()

    # Log transform
    log_prices = [math.log(p) for p in prices]
    sorted_log = sorted(log_prices)

    q1 = compute_percentile(sorted_log, 0.25)
    q3 = compute_percentile(sorted_log, 0.75)
    iqr = q3 - q1

    # Zero dispersion check (e.g. all prices identical)
    if iqr <= 1e-6:
        return set()

    lower_fence = q1 - k * iqr
    upper_fence = q3 + k * iqr

    outlier_indices = set()
    for idx, lp in enumerate(log_prices):
        if lp < lower_fence or lp > upper_fence:
            outlier_indices.add(idx)

    return outlier_indices


def identify_outlier_indices_mad(
    prices: Sequence[float],
    threshold: float = 3.5,
    min_sample_size: int = 4,
) -> Set[int]:
    """
    Identify outlier indices using Median Absolute Deviation (MAD) on log prices.

    Args:
        prices: List of positive float prices.
        threshold: Modified z-score threshold (standard is 3.5).
        min_sample_size: Minimum sample size required.

    Returns:
        Set of indices in `prices` that are flagged as outliers.
    """
    n = len(prices)
    if n < min_sample_size:
        return set()

    log_prices = [math.log(p) for p in prices]
    sorted_log = sorted(log_prices)
    med = compute_median(sorted_log)

    abs_deviations = sorted([abs(lp - med) for lp in log_prices])
    mad = compute_median(abs_deviations)

    # Zero dispersion check
    if mad <= 1e-6:
        return set()

    outlier_indices = set()
    for idx, lp in enumerate(log_prices):
        # 0.6745 is the consistency constant for standard normal distribution
        mod_z = 0.6745 * abs(lp - med) / mad
        if mod_z > threshold:
            outlier_indices.add(idx)

    return outlier_indices


def detect_outliers_by_relative(
    quotes: Sequence[FareQuote],
    mad_threshold: float = 5.0,
    min_sample_size: int = 5,
) -> Set[int]:
    """
    Flag extreme PERIOD-TO-PERIOD price movements, per carrier.

    This is the basis a price index actually needs. Each carrier's own series
    within a (route, advance_window, fare_class) stratum is ordered by
    departure date, log relatives ln(p_t / p_{t-1}) are computed, and relatives
    that are extreme against that carrier's own history are flagged.

    Why not the cross-section: comparing carriers against each other on one day
    flags a carrier for being *priced differently from its competitors*. That
    is a real market feature -- Air India costing more than IndiGo is a genuine
    price, not a data error -- and excluding it biases the index toward the
    cheapest carrier. Eurostat and ONS guidance for scraped price data screens
    period-to-period relatives, not cross-vendor level differences.

    The failure mode this replaces is concrete: once regulatory tariff-band
    fares (~INR 14,000) sat in the same daily group as market fares
    (~INR 5,000), the cross-sectional fence was fitting a bimodal sample and
    flagging essentially at random.

    Returns the set of indices in ``quotes`` to flag.
    """
    SeriesKey = Tuple[str, str, int, str, str]
    series: Dict[SeriesKey, List[Tuple[date, int, float]]] = {}

    for idx, q in enumerate(quotes):
        if q.total_fare_inr is None or q.total_fare_inr <= 0:
            continue
        key: SeriesKey = (
            q.origin_iata.upper(),
            q.destination_iata.upper(),
            q.advance_window_days,
            q.carrier_iata.upper(),
            q.fare_class.title(),
        )
        series.setdefault(key, []).append((q.departure_date, idx, q.total_fare_inr))

    flagged: Set[int] = set()

    for observations in series.values():
        if len(observations) < min_sample_size:
            continue
        observations.sort(key=lambda t: (t[0], t[1]))

        log_relatives: List[float] = []
        relative_owner: List[int] = []
        for i in range(1, len(observations)):
            prev_price = observations[i - 1][2]
            curr_price = observations[i][2]
            if prev_price <= 0 or curr_price <= 0:
                continue
            log_relatives.append(math.log(curr_price / prev_price))
            relative_owner.append(observations[i][1])

        if len(log_relatives) < min_sample_size - 1:
            continue

        med = compute_median(sorted(log_relatives))
        mad = compute_median(sorted(abs(lr - med) for lr in log_relatives))
        if mad <= 1e-6:
            continue

        for lr, owner_idx in zip(log_relatives, relative_owner):
            if 0.6745 * abs(lr - med) / mad > mad_threshold:
                flagged.add(owner_idx)

    return flagged


def detect_outliers(
    quotes: Sequence[FareQuote],
    method: str = "relative",
    k: float = 2.0,
    mad_threshold: float = 3.5,
    min_sample_size: int = 4,
) -> Tuple[List[FareQuote], int]:
    """
    Tag statistical outliers, never delete them.

    Args:
        quotes: Sequence of FareQuote objects.
        method:
            ``"relative"`` (default) screens each carrier's own period-to-period
            price movements -- the basis appropriate to a price index.
            ``"tukey"`` and ``"mad"`` screen the daily CROSS-SECTION of carriers
            on one route/window/day. Those flag legitimate carrier price
            dispersion as error; keep them for diagnostics, not for production
            index input.
        k: Tukey fence multiplier (cross-sectional methods only).
        mad_threshold: Modified z-score threshold.
        min_sample_size: Minimum observations required before screening.

    Returns:
        (result_quotes, total_outliers_flagged)
    """
    if method.lower() == "relative":
        flagged_indices = detect_outliers_by_relative(
            quotes,
            mad_threshold=max(mad_threshold, 5.0),
            min_sample_size=max(min_sample_size, 5),
        )
        results: List[FareQuote] = []
        outlier_count = 0
        for idx, q in enumerate(quotes):
            if idx in flagged_indices:
                outlier_count += 1
                results.append(replace(q, quality_flag="outlier"))
            else:
                results.append(q)
        return results, outlier_count

    # Cross-sectional methods (diagnostic).
    SegmentKey = Tuple[str, str, int, date, str]
    segments: Dict[SegmentKey, List[int]] = {}

    for idx, q in enumerate(quotes):
        # Only evaluate non-sold-out, valid positive quotes
        if q.total_fare_inr is not None and q.total_fare_inr > 0:
            key: SegmentKey = (
                q.origin_iata.upper(),
                q.destination_iata.upper(),
                q.advance_window_days,
                q.departure_date,
                q.fare_class.title(),
            )
            segments.setdefault(key, []).append(idx)

    flagged_indices = set()

    for seg_indices in segments.values():
        if len(seg_indices) < min_sample_size:
            continue

        seg_prices = [quotes[i].total_fare_inr for i in seg_indices]  # type: ignore

        if method.lower() == "mad":
            out_relative = identify_outlier_indices_mad(
                seg_prices,
                threshold=mad_threshold,
                min_sample_size=min_sample_size,
            )
        else:
            out_relative = identify_outlier_indices_tukey(
                seg_prices,
                k=k,
                min_sample_size=min_sample_size,
            )

        for r_idx in out_relative:
            flagged_indices.add(seg_indices[r_idx])

    # Construct result quotes, tagging outliers
    results: List[FareQuote] = []
    outlier_count = 0

    for idx, q in enumerate(quotes):
        if idx in flagged_indices:
            outlier_count += 1
            results.append(replace(q, quality_flag="outlier"))
        else:
            results.append(q)

    return results, outlier_count

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


def detect_outliers(
    quotes: Sequence[FareQuote],
    method: str = "tukey",
    k: float = 2.0,
    mad_threshold: float = 3.5,
    min_sample_size: int = 4,
) -> Tuple[List[FareQuote], int]:
    """
    Detect statistical outliers across quotes grouped by market segment:
    (origin_iata, destination_iata, advance_window_days, departure_date, fare_class).

    Args:
        quotes: Sequence of FareQuote objects.
        method: "tukey" (default) or "mad".
        k: Multiplier for Tukey fence (default 2.0).
        mad_threshold: Threshold for MAD modified z-score (default 3.5).
        min_sample_size: Minimum segment size required (default 4).

    Returns:
        (result_quotes, total_outliers_flagged)
    """
    # Group quotes by market segment
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

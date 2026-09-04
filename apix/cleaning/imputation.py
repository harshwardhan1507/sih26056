"""
Missing price and sold-out flight imputation module.

CPI Domain Rules (Handbook §4.2c, §6.2, §6.3):
  1. Unimputed Principle: By default, sold-out flights remain missing prices
     (total_fare_inr = None, quality_flag = 'sold_out'). In matched-sample Jevons
     elementary aggregation, they cleanly drop out of that day's ratio.
  2. Imputation Methods:
     - "class_mean": Imputes the missing carrier price using the geometric relative
       of surviving matched carriers for that market segment:
         P_hat(i, t) = P(i, t-1) * (prod_{j in Common} P(j, t) / P(j, t-1))^(1/n)
     - "carry_forward": Imputes using the previous period's transacted price P(i, t-1).
  3. Mandatory Provenance Tracking:
     Every imputed quote MUST explicitly carry:
       collection_method = "imputed"
       quality_flag = "imputed"
     This guarantees transparency for MoSPI / NSO statistical audits.
"""

from __future__ import annotations

import math
from dataclasses import replace
from datetime import date
from typing import Dict, List, Optional, Sequence, Set, Tuple

from apix.collector.adapters.base import FareQuote


def impute_missing_quotes(
    quotes: Sequence[FareQuote],
    strategy: str = "class_mean",
    impute_outliers: bool = True,
) -> Tuple[List[FareQuote], int]:
    """
    Impute missing prices for sold-out flights or flagged outliers across chronological dates.

    Args:
        quotes: Sequence of FareQuote objects.
        strategy: "class_mean" (default) or "carry_forward".
        impute_outliers: Whether quotes flagged as 'outlier' should be imputed.

    Returns:
        (result_quotes, imputed_count)
    """
    if strategy not in ("class_mean", "carry_forward"):
        raise ValueError(f"Unknown imputation strategy: '{strategy}' (expected 'class_mean' or 'carry_forward')")

    # Group by market segment: (origin, destination, advance_window_days, fare_class)
    # Inside segment: map departure_date -> list of quotes
    SegmentKey = Tuple[str, str, int, str]
    segments: Dict[SegmentKey, Dict[date, List[FareQuote]]] = {}

    for q in quotes:
        seg_key: SegmentKey = (
            q.origin_iata.upper(),
            q.destination_iata.upper(),
            q.advance_window_days,
            q.fare_class.title(),
        )
        segments.setdefault(seg_key, {}).setdefault(q.departure_date, []).append(q)

    all_result_quotes: List[FareQuote] = []
    total_imputed = 0

    for seg_key, date_map in segments.items():
        sorted_dates = sorted(date_map.keys())

        # Tracks carrier -> previous valid price
        prev_prices: Dict[str, float] = {}

        for dep_date in sorted_dates:
            day_quotes = date_map[dep_date]

            # Collect today's valid carriers and prices
            today_valid: Dict[str, float] = {}
            for q in day_quotes:
                if q.total_fare_inr is not None and q.total_fare_inr > 0:
                    if q.quality_flag == "ok" or (q.quality_flag == "outlier" and not impute_outliers):
                        today_valid[q.carrier_iata.upper()] = q.total_fare_inr

            # Calculate common carrier geometric relative for class-mean strategy
            common_carriers = set(today_valid.keys()) & set(prev_prices.keys())
            geom_relative: Optional[float] = None

            if len(common_carriers) > 0 and strategy == "class_mean":
                log_sum = sum(
                    math.log(today_valid[c] / prev_prices[c])
                    for c in common_carriers
                    if prev_prices[c] > 0 and today_valid[c] > 0
                )
                geom_relative = math.exp(log_sum / len(common_carriers))

            # Process quotes for today
            for q in day_quotes:
                carrier = q.carrier_iata.upper()
                needs_imputation = False

                if q.quality_flag == "sold_out" or q.total_fare_inr is None:
                    needs_imputation = True
                elif impute_outliers and q.quality_flag == "outlier":
                    needs_imputation = True

                if needs_imputation and carrier in prev_prices:
                    # Carrier was seen on previous day -> can impute
                    prev_p = prev_prices[carrier]
                    if strategy == "class_mean" and geom_relative is not None:
                        imputed_p = round(prev_p * geom_relative, 2)
                    else:
                        imputed_p = round(prev_p, 2)

                    imputed_quote = replace(
                        q,
                        total_fare_inr=imputed_p,
                        collection_method="imputed",
                        quality_flag="imputed",
                    )
                    all_result_quotes.append(imputed_quote)
                    total_imputed += 1
                    # Update price tracking with imputed price
                    prev_prices[carrier] = imputed_p
                else:
                    all_result_quotes.append(q)
                    if q.total_fare_inr is not None and q.total_fare_inr > 0 and q.quality_flag == "ok":
                        prev_prices[carrier] = q.total_fare_inr

    return all_result_quotes, total_imputed

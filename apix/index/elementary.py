"""
Jevons elementary index — geometric mean of price relatives.

Why Jevons and not a simple average: airfares swing 200-400% intraday.
An arithmetic mean (Carli/Dutot) gets dragged around by that dispersion.
Jevons is invariant to which period you call the "base" and is the
standard NSI choice for scraped/dynamic price data (Eurostat, ONS).

This is a CHAINED, matched-sample index: on each day we only compare
carriers whose price is available on BOTH that day and the reference day.
A sold-out flight just drops out of that day's comparison instead of
being treated as a price of zero (see handbook §4.2c).

Gap handling
------------
Collection days go missing (scheduler skipped, source outage, route not
served). The reference for a comparison is therefore the most recent day
that actually had usable prices, not blindly ``t-1``. Without this, one
missing day silently erases two days of genuine price movement from the
chain and the loss is permanent -- the index never recovers it.

A day with no usable prices at all leaves the index level flat and keeps
the previous reference, so the next day with data bridges the gap. A day
whose carriers do not overlap the reference at all cannot yield a valid
relative, so the chain restarts from that day's level (no movement is
invented across a gap that cannot be measured).
"""

import math


def jevons_ratio(prices_today: dict[str, float], prices_yesterday: dict[str, float]) -> float | None:
    """
    prices_today / prices_yesterday: {carrier_iata: price}
    Returns the geometric mean of today/yesterday price relatives for
    carriers present in both days, or None if there's no overlap.
    """
    common = set(prices_today) & set(prices_yesterday)
    if not common:
        return None

    log_sum = 0.0
    n_valid = 0
    for carrier in common:
        p_t = prices_today[carrier]
        p_y = prices_yesterday[carrier]
        if p_t is None or p_y is None or p_t <= 0 or p_y <= 0:
            continue
        log_sum += math.log(p_t / p_y)
        n_valid += 1

    if n_valid == 0:
        return None
    return math.exp(log_sum / n_valid)


def _has_usable_prices(prices: dict[str, float]) -> bool:
    """True if at least one carrier has a positive, non-missing price."""
    return any(p is not None and p > 0 for p in prices.values())


def build_elementary_index(
    daily_prices: list[dict[str, float]],
    base_value: float = 100.0,
) -> list[float]:
    """
    daily_prices: chronological list of {carrier_iata: price} dicts, one per day,
                  for a single (route, advance_window) elementary aggregate.
                  Days with no observations should be passed as ``{}`` so the
                  series stays aligned to a dense calendar.
    Returns the chained index series, same length, starting at base_value.
    """
    if not daily_prices:
        return []

    index = [base_value]
    reference = daily_prices[0]

    for t in range(1, len(daily_prices)):
        today = daily_prices[t]
        prev_level = index[-1]

        if not _has_usable_prices(today):
            # No observations at all: hold the level, keep the old reference
            # so a later day can still bridge across this gap.
            index.append(prev_level)
            continue

        ratio = jevons_ratio(today, reference)
        if ratio is None:
            # Today has prices but shares no carrier with the reference, so
            # no valid relative exists. Hold the level and re-anchor.
            index.append(prev_level)
        else:
            index.append(prev_level * ratio)
        reference = today

    return index


def observation_counts(daily_prices: list[dict[str, float]]) -> list[int]:
    """
    Number of usable carrier observations per day. Surfaced alongside the
    index so consumers can see how thin a given day's matched sample was.
    """
    return [
        sum(1 for p in day.values() if p is not None and p > 0)
        for day in daily_prices
    ]

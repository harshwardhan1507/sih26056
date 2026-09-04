"""
Jevons elementary index — geometric mean of price relatives.

Why Jevons and not a simple average: airfares swing 200-400% intraday.
An arithmetic mean (Carli/Dutot) gets dragged around by that dispersion.
Jevons is invariant to which period you call the "base" and is the
standard NSI choice for scraped/dynamic price data (Eurostat, ONS).

This is a CHAINED, matched-sample index: on each day we only compare
carriers whose price is available on BOTH today and yesterday. A
sold-out flight just drops out of that day's comparison instead of
being treated as a price of zero (see handbook §4.2c).
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
    for carrier in common:
        p_t = prices_today[carrier]
        p_y = prices_yesterday[carrier]
        if p_t is None or p_y is None or p_t <= 0 or p_y <= 0:
            continue
        log_sum += math.log(p_t / p_y)

    n = len(common)
    if n == 0:
        return None
    return math.exp(log_sum / n)


def build_elementary_index(daily_prices: list[dict[str, float]], base_value: float = 100.0) -> list[float]:
    """
    daily_prices: chronological list of {carrier_iata: price} dicts, one per day,
                  for a single (route, advance_window) elementary aggregate.
    Returns the chained index series, same length, starting at base_value.
    """
    index = [base_value]
    for t in range(1, len(daily_prices)):
        ratio = jevons_ratio(daily_prices[t], daily_prices[t - 1])
        prev = index[-1]
        index.append(prev if ratio is None else prev * ratio)
    return index

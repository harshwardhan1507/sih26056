"""
Chained Laspeyres aggregation over elementary indices.

Combines per-(route, advance_window) Jevons indices into one APIx number,
using fixed weights (DGCA passenger-traffic share, placeholder here —
replace with the real Vonter/india-aviation-traffic derived weights).

Chained: weights are re-fixed at each rebase point rather than held
constant forever, so the index doesn't go stale as route popularity shifts.
"""


def build_aggregate_index(
    elementary_indices: dict[str, list[float]],
    weights: dict[str, float],
) -> list[float]:
    """
    elementary_indices: {"DEL-BOM|30": [100.0, 100.4, ...], ...} — equal-length series
    weights: {"DEL-BOM|30": 0.18, ...} — should sum to ~1.0 across all keys
    Returns the weighted aggregate index series (chained day-over-day).
    """
    keys = list(elementary_indices.keys())
    n_days = len(next(iter(elementary_indices.values())))
    total_weight = sum(weights.get(k, 0.0) for k in keys) or 1.0

    aggregate = [100.0]
    for t in range(1, n_days):
        weighted_relative = 0.0
        for k in keys:
            w = weights.get(k, 0.0) / total_weight
            series = elementary_indices[k]
            relative = series[t] / series[t - 1] if series[t - 1] else 1.0
            weighted_relative += w * relative
        aggregate.append(aggregate[-1] * weighted_relative)
    return aggregate

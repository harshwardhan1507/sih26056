"""
Deduplication module for APIx fare quote collection.

Handles duplicate observations generated from:
  - Multi-pass scraping or overlapping collection runs
  - Multi-source convergence (e.g. both API and scraper capturing the same flight)
  - Retried HTTP calls or redundant adapter queries

Implements a deterministic tie-breaking hierarchy:
  1. Source Tier Priority: api > tariff_sheet > scrape > simulated > imputed
  2. Quality Flag Priority: ok > imputed > outlier > sold_out
  3. Timestamp Recency: Latest collected_at_utc wins
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Dict, List, Sequence, Tuple

from apix.collector.adapters.base import FareQuote

# Source hierarchy: higher numerical rank takes precedence
SOURCE_TIER_PRIORITY: Dict[str, int] = {
    "api": 4,
    "tariff_sheet": 3,
    "scrape": 2,
    "simulated": 1,
    "imputed": 0,
}

# Quality flag hierarchy: higher numerical rank takes precedence
QUALITY_FLAG_PRIORITY: Dict[str, int] = {
    "ok": 3,
    "imputed": 2,
    "outlier": 1,
    "sold_out": 0,
}


def quote_identity_key(quote: FareQuote) -> Tuple[str, str, date, int, str, str]:
    """
    Generate canonical identity key for a fare observation:
    (origin_iata, destination_iata, departure_date, advance_window_days, carrier_iata, fare_class)
    """
    return (
        quote.origin_iata.upper(),
        quote.destination_iata.upper(),
        quote.departure_date,
        quote.advance_window_days,
        quote.carrier_iata.upper(),
        quote.fare_class.title(),
    )


def quote_precedence_score(quote: FareQuote) -> Tuple[int, int, datetime]:
    """
    Calculates a comparable score tuple for tie-breaking duplicates.
    Higher values win.
    Tuple: (source_priority, quality_priority, collected_at_utc)
    """
    src_score = SOURCE_TIER_PRIORITY.get(quote.collection_method.lower(), -1)
    q_score = QUALITY_FLAG_PRIORITY.get(quote.quality_flag.lower(), -1)
    col_time = quote.collected_at_utc
    return (src_score, q_score, col_time)


def deduplicate_quotes(quotes: Sequence[FareQuote]) -> Tuple[List[FareQuote], int]:
    """
    Deduplicate a sequence of FareQuotes. When duplicate quotes exist for the same
    carrier/route/departure-date/window/class, retains the highest-precedence quote.

    Returns:
        (unique_quotes, duplicates_dropped_count)
    """
    seen: Dict[Tuple, FareQuote] = {}
    duplicates_dropped = 0

    for q in quotes:
        key = quote_identity_key(q)
        if key not in seen:
            seen[key] = q
        else:
            duplicates_dropped += 1
            existing = seen[key]
            # Replace existing if current quote has strictly higher precedence
            if quote_precedence_score(q) > quote_precedence_score(existing):
                seen[key] = q

    return list(seen.values()), duplicates_dropped

"""
FareResolver — Central multi-tier resolution layer for airfare collection.

Routes queries through a prioritized source chain:
  Tier 1: Licensed APIs (TripJack / TBO / Travelpayouts)
  Tier 2: Mandated tariff sheets (DGCA Circular 2 of 2010 / Rule 135)
  Tier 3: Polite web scrapers
  Tier 4: Simulated / cached fallback (SimulatedFareSource)

Key Design Principles:
1. Per-Carrier Resolution: If a primary source covers only a subset of carriers,
   the resolver seamlessly queries subsequent tiers for only the remaining missing carriers.
2. Resilience: Any exception in a primary source is caught, logged, and bypassed
   without terminating collection.
3. Fallback Visibility: Tracks quote resolution counts per source/tier to provide
   real-time visibility into the proportion of real vs. fallback data.
4. Provenance Preservation: Returned FareQuote objects maintain their native
   source_id, collection_method, and quality_flag.
"""

from dataclasses import dataclass, field
from datetime import date
import logging
from typing import Sequence

from .adapters.base import FareQuote, FareSource
from .adapters.simulated import SimulatedFareSource


@dataclass
class ResolverMetrics:
    """Metrics tracking quote resolution across sources and tiers."""
    total_requested: int = 0
    resolved_by_source: dict[str, int] = field(default_factory=dict)
    fallback_invocations: int = 0

    def to_dict(self) -> dict:
        total_resolved = sum(self.resolved_by_source.values())
        return {
            "total_requested": self.total_requested,
            "total_resolved": total_resolved,
            "resolved_by_source": dict(self.resolved_by_source),
            "fallback_invocations": self.fallback_invocations,
        }


class FareResolver(FareSource):
    """
    Central fare resolution adapter.

    Resolves requested quotes across primary sources, falling back to
    SimulatedFareSource for any carriers that remain unquoted.
    """

    source_id = "fare_resolver_v1"
    collection_method = "resolver"

    def __init__(
        self,
        primary_sources: Sequence[FareSource] = (),
        fallback_source: FareSource | None = None,
    ) -> None:
        """
        Initialize the resolver.

        Args:
            primary_sources: Ordered sequence of FareSource instances to query first.
                             Defaults to empty list in v1 (all calls fall through to fallback).
            fallback_source: Source to query for carriers missing after primary sources.
                             Defaults to SimulatedFareSource().
        """
        self.primary_sources = list(primary_sources)
        self.fallback_source = fallback_source or SimulatedFareSource()
        self.metrics = ResolverMetrics()
        self.logger = logging.getLogger(__name__)

    def get_quotes(
        self,
        origin: str,
        destination: str,
        as_of_date: date,
        advance_window_days: int,
        carriers: list[str],
    ) -> list[FareQuote]:
        """
        Obtain fare quotes for the requested route, window, and carriers.

        Performs per-carrier resolution: queries primary sources in order,
        and requests only remaining unquoted carriers from subsequent tiers/fallback.
        """
        normalized_carriers = [c.strip().upper() for c in carriers]
        self.metrics.total_requested += len(normalized_carriers)
        resolved_quotes: list[FareQuote] = []
        remaining_carriers = set(normalized_carriers)

        # 1. Query primary sources sequentially for remaining unquoted carriers
        for source in self.primary_sources:
            if not remaining_carriers:
                break
            try:
                quotes = source.get_quotes(
                    origin=origin,
                    destination=destination,
                    as_of_date=as_of_date,
                    advance_window_days=advance_window_days,
                    carriers=list(remaining_carriers),
                )
                for q in quotes:
                    c_code = q.carrier_iata.strip().upper()
                    if c_code in remaining_carriers:
                        resolved_quotes.append(q)
                        remaining_carriers.remove(c_code)
                        self.metrics.resolved_by_source[source.source_id] = (
                            self.metrics.resolved_by_source.get(source.source_id, 0) + 1
                        )
            except Exception as exc:
                self.logger.warning(
                    "Primary source '%s' raised exception for %s-%s (window %d): %s",
                    source.source_id,
                    origin,
                    destination,
                    advance_window_days,
                    exc,
                )

        # 2. Fall back for any carriers that remain unquoted
        if remaining_carriers:
            self.metrics.fallback_invocations += 1
            try:
                fallback_quotes = self.fallback_source.get_quotes(
                    origin=origin,
                    destination=destination,
                    as_of_date=as_of_date,
                    advance_window_days=advance_window_days,
                    carriers=list(remaining_carriers),
                )
                for q in fallback_quotes:
                    c_code = q.carrier_iata.strip().upper()
                    if c_code in remaining_carriers:
                        resolved_quotes.append(q)
                        remaining_carriers.remove(c_code)
                        self.metrics.resolved_by_source[self.fallback_source.source_id] = (
                            self.metrics.resolved_by_source.get(self.fallback_source.source_id, 0) + 1
                        )
            except Exception as exc:
                self.logger.error(
                    "Fallback source '%s' raised exception for %s-%s (window %d): %s",
                    self.fallback_source.source_id,
                    origin,
                    destination,
                    advance_window_days,
                    exc,
                )

        return resolved_quotes

    def get_metrics_summary(self) -> dict:
        """Return a dictionary summarizing resolution metrics."""
        return self.metrics.to_dict()

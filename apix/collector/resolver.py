"""
FareResolver — Central multi-tier resolution layer for airfare collection.

Routes queries through a prioritized source chain:
  Tier 1: Licensed APIs (TripJack / TBO / Travelpayouts)
  Tier 2: Mandated tariff sheets (DGCA Circular 2 of 2010 / Rule 135)
  Tier 3: HAR-replay / polite web collection
  Tier 4: Simulated fallback (SimulatedFareSource)

Key design principles
---------------------
1. Per-carrier resolution: if a primary source covers only some carriers, the
   remaining carriers are requested from subsequent tiers and merged.
2. Deterministic order: carriers are requested and returned in the caller's
   order. This used to iterate a ``set``, so row order varied between
   processes (PYTHONHASHSEED) and "reproducible" output files were not.
3. Contract enforcement: a quote is accepted only if it actually answers the
   question that was asked -- right route, right window, right carrier. A
   mismatched quote is dropped and logged, not silently indexed. The project's
   hard rule that advance-purchase windows are never crossed was previously
   unenforced at the one place every quote passes through.
4. Resilience: a failing source is bypassed, and a source that keeps failing
   is tripped out of the chain by a circuit breaker instead of being retried
   on every route.
5. Provenance preservation: returned quotes keep their native source_id,
   collection_method and quality_flag.
"""

from dataclasses import dataclass, field
from datetime import date
import logging
from typing import Sequence

from .adapters.base import FareQuote, FareSource
from .adapters.simulated import SimulatedFareSource
from .adapters.tariff_sheet import IndiGoTariffSheetSource
from .compliance.circuit_breaker import CircuitBreaker, CircuitOpenError


@dataclass
class ResolverMetrics:
    """Metrics tracking quote resolution across sources and tiers."""
    total_requested: int = 0
    resolved_by_source: dict[str, int] = field(default_factory=dict)
    fallback_invocations: int = 0
    unresolved: int = 0
    rejected_contract_violations: int = 0
    source_errors: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict:
        total_resolved = sum(self.resolved_by_source.values())
        return {
            "total_requested": self.total_requested,
            "total_resolved": total_resolved,
            "resolved_by_source": dict(self.resolved_by_source),
            "fallback_invocations": self.fallback_invocations,
            "unresolved": self.unresolved,
            "rejected_contract_violations": self.rejected_contract_violations,
            "source_errors": dict(self.source_errors),
        }


class FareResolver(FareSource):
    """
    Central fare resolution adapter.

    Resolves requested quotes across primary sources, falling back to
    SimulatedFareSource for any carriers that remain unquoted.
    """

    source_id = "fare_resolver_v1"
    # The resolver never stamps its own method onto a quote -- each quote keeps
    # the method of the source that produced it. Declared here only to satisfy
    # the FareSource contract, using a value from the accepted vocabulary.
    collection_method = "simulated"

    def __init__(
        self,
        primary_sources: Sequence[FareSource] | None = None,
        fallback_source: FareSource | None = None,
        *,
        failure_threshold: int = 3,
        cooldown_seconds: float = 300.0,
    ) -> None:
        """
        Args:
            primary_sources: Ordered sources to query first. Defaults to
                             [IndiGoTariffSheetSource(use_fixture=True)] (Tier 2).
                             Pass () to disable primary sources.
            fallback_source: Queried for carriers still missing. Defaults to
                             SimulatedFareSource().
            failure_threshold: Consecutive failures before a source is tripped out.
            cooldown_seconds: How long a tripped source stays out of the chain.
        """
        if primary_sources is None:
            self.primary_sources = [IndiGoTariffSheetSource(use_fixture=True)]
        else:
            self.primary_sources = list(primary_sources)
        self.fallback_source = fallback_source or SimulatedFareSource()
        self.metrics = ResolverMetrics()
        self.logger = logging.getLogger(__name__)

        self._breakers: dict[str, CircuitBreaker] = {
            src.source_id: CircuitBreaker(
                src.source_id,
                failure_threshold=failure_threshold,
                cooldown_seconds=cooldown_seconds,
            )
            for src in self.primary_sources
        }

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

        Queries primary sources in order, requesting only the still-missing
        carriers from each subsequent tier, then the fallback. Results are
        returned in the caller's carrier order.
        """
        orig = origin.strip().upper()
        dest = destination.strip().upper()

        # Preserve caller order, drop duplicates.
        requested: list[str] = []
        for c in carriers:
            code = c.strip().upper()
            if code and code not in requested:
                requested.append(code)

        self.metrics.total_requested += len(requested)
        resolved: dict[str, FareQuote] = {}

        for source in self.primary_sources:
            remaining = [c for c in requested if c not in resolved]
            if not remaining:
                break
            self._query(
                source, orig, dest, as_of_date, advance_window_days,
                remaining, resolved, is_fallback=False,
            )

        remaining = [c for c in requested if c not in resolved]
        if remaining:
            self.metrics.fallback_invocations += 1
            self._query(
                self.fallback_source, orig, dest, as_of_date, advance_window_days,
                remaining, resolved, is_fallback=True,
            )

        still_missing = [c for c in requested if c not in resolved]
        if still_missing:
            self.metrics.unresolved += len(still_missing)
            self.logger.warning(
                "No quote resolved for %s on %s-%s T+%d (every tier declined).",
                still_missing, orig, dest, advance_window_days,
            )

        return [resolved[c] for c in requested if c in resolved]

    def _query(
        self,
        source: FareSource,
        origin: str,
        destination: str,
        as_of_date: date,
        advance_window_days: int,
        carriers: list[str],
        resolved: dict[str, FareQuote],
        *,
        is_fallback: bool,
    ) -> None:
        """Query one source and merge any quotes that satisfy the contract."""
        breaker = self._breakers.get(source.source_id)

        try:
            call = lambda: source.get_quotes(
                origin=origin,
                destination=destination,
                as_of_date=as_of_date,
                advance_window_days=advance_window_days,
                carriers=list(carriers),
            )
            quotes = breaker.call(call) if breaker is not None else call()
        except CircuitOpenError:
            self.logger.debug(
                "Skipping '%s' for %s-%s T+%d: circuit open.",
                source.source_id, origin, destination, advance_window_days,
            )
            return
        except Exception as exc:
            self.metrics.source_errors[source.source_id] = (
                self.metrics.source_errors.get(source.source_id, 0) + 1
            )
            log = self.logger.error if is_fallback else self.logger.warning
            log(
                "Source '%s' raised for %s-%s (T+%d): %s",
                source.source_id, origin, destination, advance_window_days, exc,
            )
            return

        wanted = set(carriers)
        for q in quotes:
            code = q.carrier_iata.strip().upper()
            if code not in wanted or code in resolved:
                continue
            if not self._satisfies_contract(q, origin, destination, advance_window_days):
                self.metrics.rejected_contract_violations += 1
                continue
            resolved[code] = q
            self.metrics.resolved_by_source[source.source_id] = (
                self.metrics.resolved_by_source.get(source.source_id, 0) + 1
            )

    def _satisfies_contract(
        self,
        quote: FareQuote,
        origin: str,
        destination: str,
        advance_window_days: int,
    ) -> bool:
        """
        A quote must answer the question that was asked.

        Crossing advance-purchase windows is a quality difference, not a price
        change, so a quote for the wrong window can never be indexed against
        this one. Same for the wrong route.
        """
        if quote.advance_window_days != advance_window_days:
            self.logger.warning(
                "Rejected quote from '%s': asked for T+%d, got T+%d (%s-%s, %s).",
                quote.source_id, advance_window_days, quote.advance_window_days,
                origin, destination, quote.carrier_iata,
            )
            return False

        q_orig = quote.origin_iata.strip().upper()
        q_dest = quote.destination_iata.strip().upper()
        if (q_orig, q_dest) != (origin, destination):
            self.logger.warning(
                "Rejected quote from '%s': asked for %s-%s, got %s-%s (%s).",
                quote.source_id, origin, destination, q_orig, q_dest,
                quote.carrier_iata,
            )
            return False

        return True

    def get_metrics_summary(self) -> dict:
        """Return a dictionary summarizing resolution metrics."""
        summary = self.metrics.to_dict()
        summary["circuit_state"] = {
            name: br.state for name, br in self._breakers.items()
        }
        return summary

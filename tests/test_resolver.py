"""
Unit tests for FareResolver (apix/collector/resolver.py).

Tests multi-tier fallback, per-carrier partial resolution, exception resilience,
provenance preservation, and telemetry tracking.
"""

from datetime import date, datetime, timezone
from pathlib import Path
import sys

# Ensure repository root is on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from apix.collector.adapters.base import FareQuote, FareSource
from apix.collector.resolver import FareResolver


class MockCarrierSource(FareSource):
    """Mock primary adapter returning quotes for specific carriers only."""

    def __init__(self, source_id: str, supported_carriers: list[str], price: float = 4999.0) -> None:
        self.source_id = source_id
        self.collection_method = "mock_api"
        self.supported_carriers = set(supported_carriers)
        self.price = price
        self.call_count = 0

    def get_quotes(
        self,
        origin: str,
        destination: str,
        as_of_date: date,
        advance_window_days: int,
        carriers: list[str],
    ) -> list[FareQuote]:
        self.call_count += 1
        quotes = []
        for c in carriers:
            if c in self.supported_carriers:
                quotes.append(
                    FareQuote(
                        collected_at_utc=datetime.now(timezone.utc),
                        departure_date=as_of_date,
                        advance_window_days=advance_window_days,
                        origin_iata=origin,
                        destination_iata=destination,
                        carrier_iata=c,
                        fare_class="Economy",
                        total_fare_inr=self.price,
                        source_id=self.source_id,
                        collection_method=self.collection_method,
                        quality_flag="ok",
                    )
                )
        return quotes


class FailingSource(FareSource):
    """Mock adapter that simulates network or parsing failures."""

    source_id = "failing_api"
    collection_method = "mock_failing"

    def get_quotes(
        self,
        origin: str,
        destination: str,
        as_of_date: date,
        advance_window_days: int,
        carriers: list[str],
    ) -> list[FareQuote]:
        raise ConnectionResetError("Remote OTA endpoint timed out")


def test_resolver_default_fallback():
    """Pure fallback behavior: with empty primary_sources, falls back entirely to SimulatedFareSource."""
    resolver = FareResolver(primary_sources=[])
    carriers = ["6E", "AI", "QP", "SG", "IX"]
    quotes = resolver.get_quotes(
        origin="DEL",
        destination="BOM",
        as_of_date=date(2026, 9, 4),
        advance_window_days=7,
        carriers=carriers,
    )

    assert len(quotes) == len(carriers)
    returned_carriers = {q.carrier_iata for q in quotes}
    assert returned_carriers == set(carriers)

    # Check provenance fields
    for q in quotes:
        assert q.source_id == "simulated_v1"
        assert q.collection_method == "simulated"
        assert q.quality_flag in ("ok", "outlier", "sold_out")
        assert q.origin_iata == "DEL"
        assert q.destination_iata == "BOM"

    metrics = resolver.get_metrics_summary()
    assert metrics["total_requested"] == 5
    assert metrics["total_resolved"] == 5
    assert metrics["resolved_by_source"].get("simulated_v1") == 5
    assert metrics["fallback_invocations"] == 1


def test_resolver_default_wires_indigo_tariff():
    """Default resolver automatically includes IndiGoTariffSheetSource in primary sources."""
    resolver = FareResolver()
    carriers = ["6E", "AI", "QP", "SG", "IX"]
    quotes = resolver.get_quotes(
        origin="DEL",
        destination="BOM",
        as_of_date=date(2026, 9, 4),
        advance_window_days=7,
        carriers=carriers,
    )

    assert len(quotes) == len(carriers)
    by_carrier = {q.carrier_iata: q for q in quotes}

    # 6E resolved via Tier 2 IndiGo tariff sheet
    assert "6E" in by_carrier
    assert by_carrier["6E"].source_id == "indigo_tariff_v1"
    assert by_carrier["6E"].collection_method == "tariff_sheet"
    assert by_carrier["6E"].quality_flag == "ok"
    assert by_carrier["6E"].total_fare_inr > 0

    # Remaining carriers resolved via Tier 4 simulator
    for c in ["AI", "QP", "SG", "IX"]:
        assert by_carrier[c].source_id == "simulated_v1"
        assert by_carrier[c].collection_method == "simulated"

    metrics = resolver.get_metrics_summary()
    assert metrics["total_requested"] == 5
    assert metrics["total_resolved"] == 5
    assert metrics["resolved_by_source"]["indigo_tariff_v1"] == 1
    assert metrics["resolved_by_source"]["simulated_v1"] == 4
    assert metrics["fallback_invocations"] == 1


def test_resolver_partial_carrier_merge():
    """Primary source only covers 6E and AI; resolver fills QP, SG, IX from fallback."""
    mock_primary = MockCarrierSource(source_id="tripjack_v1", supported_carriers=["6E", "AI"], price=5200.0)
    resolver = FareResolver(primary_sources=[mock_primary])

    carriers = ["6E", "AI", "QP", "SG", "IX"]
    quotes = resolver.get_quotes(
        origin="DEL",
        destination="BOM",
        as_of_date=date(2026, 9, 4),
        advance_window_days=7,
        carriers=carriers,
    )

    assert len(quotes) == 5
    by_carrier = {q.carrier_iata: q for q in quotes}

    # 6E and AI from primary
    assert by_carrier["6E"].source_id == "tripjack_v1"
    assert by_carrier["6E"].collection_method == "mock_api"
    assert by_carrier["6E"].total_fare_inr == 5200.0

    assert by_carrier["AI"].source_id == "tripjack_v1"
    assert by_carrier["AI"].collection_method == "mock_api"

    # Remaining carriers filled by fallback
    for c in ["QP", "SG", "IX"]:
        assert by_carrier[c].source_id == "simulated_v1"
        assert by_carrier[c].collection_method == "simulated"

    metrics = resolver.get_metrics_summary()
    assert metrics["resolved_by_source"]["tripjack_v1"] == 2
    assert metrics["resolved_by_source"]["simulated_v1"] == 3
    assert metrics["fallback_invocations"] == 1


def test_resolver_resilience_to_exceptions():
    """If a primary source crashes, resolver logs warning and cleanly falls back."""
    failing = FailingSource()
    resolver = FareResolver(primary_sources=[failing])

    carriers = ["6E", "AI"]
    quotes = resolver.get_quotes(
        origin="DEL",
        destination="BOM",
        as_of_date=date(2026, 9, 4),
        advance_window_days=7,
        carriers=carriers,
    )

    # All quotes still resolved via fallback
    assert len(quotes) == 2
    for q in quotes:
        assert q.source_id == "simulated_v1"

    metrics = resolver.get_metrics_summary()
    assert metrics["resolved_by_source"]["simulated_v1"] == 2
    assert "failing_api" not in metrics["resolved_by_source"]
    assert metrics["fallback_invocations"] == 1


def test_resolver_full_primary_success():
    """If primary source covers all carriers, fallback is never invoked."""
    mock_primary = MockCarrierSource(
        source_id="full_api",
        supported_carriers=["6E", "AI", "QP", "SG", "IX"],
    )
    resolver = FareResolver(primary_sources=[mock_primary])

    quotes = resolver.get_quotes(
        origin="DEL",
        destination="BOM",
        as_of_date=date(2026, 9, 4),
        advance_window_days=7,
        carriers=["6E", "AI", "QP", "SG", "IX"],
    )

    assert len(quotes) == 5
    for q in quotes:
        assert q.source_id == "full_api"

    metrics = resolver.get_metrics_summary()
    assert metrics["resolved_by_source"]["full_api"] == 5
    assert "simulated_v1" not in metrics["resolved_by_source"]
    assert metrics["fallback_invocations"] == 0


def test_resolver_case_insensitive_carrier_matching():
    """Verify carrier codes match case-insensitively across adapter responses."""
    mock_primary = MockCarrierSource(
        source_id="primary_api",
        supported_carriers=["6E"],
    )
    resolver = FareResolver(primary_sources=[mock_primary])
    # Pass lowercase carrier codes
    quotes = resolver.get_quotes(
        origin="DEL",
        destination="BOM",
        as_of_date=date(2026, 9, 4),
        advance_window_days=7,
        carriers=["6e", "ai"],
    )
    assert len(quotes) == 2
    by_carrier = {q.carrier_iata.upper(): q for q in quotes}
    assert "6E" in by_carrier
    assert "AI" in by_carrier
    assert by_carrier["6E"].source_id == "primary_api"
    assert by_carrier["AI"].source_id == "simulated_v1"


if __name__ == "__main__":
    test_resolver_default_fallback()
    test_resolver_default_wires_indigo_tariff()
    test_resolver_partial_carrier_merge()
    test_resolver_resilience_to_exceptions()
    test_resolver_full_primary_success()
    test_resolver_case_insensitive_carrier_matching()
    print("All FareResolver unit tests passed successfully!")


# ---------------------------------------------------------------------------
# Contract enforcement & determinism regression tests
# ---------------------------------------------------------------------------

class _WrongWindowSource(FareSource):
    """A buggy adapter that answers with the wrong advance window."""
    source_id = "wrong_window_v1"
    collection_method = "api"

    def get_quotes(self, origin, destination, as_of_date, advance_window_days, carriers):
        return [FareQuote(
            collected_at_utc=datetime.now(timezone.utc),
            departure_date=as_of_date,
            advance_window_days=advance_window_days + 7,   # wrong window
            origin_iata=origin, destination_iata=destination,
            carrier_iata="6E", fare_class="Economy",
            total_fare_inr=4321.0,
            source_id=self.source_id,
            collection_method=self.collection_method,
            quality_flag="ok",
        )]


class _WrongRouteSource(FareSource):
    """A buggy adapter that answers about a different route."""
    source_id = "wrong_route_v1"
    collection_method = "api"

    def get_quotes(self, origin, destination, as_of_date, advance_window_days, carriers):
        return [FareQuote(
            collected_at_utc=datetime.now(timezone.utc),
            departure_date=as_of_date,
            advance_window_days=advance_window_days,
            origin_iata="CCU", destination_iata="GOI",     # wrong route
            carrier_iata="6E", fare_class="Economy",
            total_fare_inr=4321.0,
            source_id=self.source_id,
            collection_method=self.collection_method,
            quality_flag="ok",
        )]


class _AlwaysFailingSource(FareSource):
    source_id = "always_fails_v1"
    collection_method = "api"

    def __init__(self):
        self.calls = 0

    def get_quotes(self, origin, destination, as_of_date, advance_window_days, carriers):
        self.calls += 1
        raise RuntimeError("upstream down")


def test_rejects_quote_for_wrong_advance_window():
    """Crossing advance windows is a quality difference, never a price change."""
    resolver = FareResolver(primary_sources=[_WrongWindowSource()])
    quotes = resolver.get_quotes("DEL", "BOM", date(2026, 9, 4), 7, ["6E"])

    assert all(q.advance_window_days == 7 for q in quotes)
    assert all(q.source_id != "wrong_window_v1" for q in quotes), (
        "A T+14 quote was accepted for a T+7 request."
    )
    assert resolver.get_metrics_summary()["rejected_contract_violations"] == 1


def test_rejects_quote_for_wrong_route():
    resolver = FareResolver(primary_sources=[_WrongRouteSource()])
    quotes = resolver.get_quotes("DEL", "BOM", date(2026, 9, 4), 7, ["6E"])

    assert all((q.origin_iata, q.destination_iata) == ("DEL", "BOM") for q in quotes)
    assert resolver.get_metrics_summary()["rejected_contract_violations"] == 1


def test_carrier_order_is_deterministic():
    """
    Output order follows the caller's carrier order.

    Resolution used to iterate a set, so row order varied between processes
    and files described as reproducible were not.
    """
    carriers = ["6E", "AI", "QP", "SG", "IX"]
    resolver = FareResolver(primary_sources=[])
    order = [q.carrier_iata for q in
             resolver.get_quotes("DEL", "BOM", date(2026, 9, 4), 7, carriers)]

    for _ in range(5):
        again = FareResolver(primary_sources=[])
        assert [q.carrier_iata for q in
                again.get_quotes("DEL", "BOM", date(2026, 9, 4), 7, carriers)] == order
    assert order == [c for c in carriers if c in order]


def test_circuit_breaker_stops_retrying_a_dead_source():
    """A source that keeps failing is tripped out instead of retried per route."""
    failing = _AlwaysFailingSource()
    resolver = FareResolver(primary_sources=[failing], failure_threshold=2)

    for _ in range(10):
        resolver.get_quotes("DEL", "BOM", date(2026, 9, 4), 7, ["6E"])

    assert failing.calls == 2, (
        f"Expected the breaker to stop calls after 2 failures, got {failing.calls}."
    )
    assert resolver.get_metrics_summary()["circuit_state"]["always_fails_v1"] == "open"


def test_unresolved_carriers_are_counted():
    """Carriers no tier could price are reported, not silently dropped."""
    resolver = FareResolver(primary_sources=[])
    resolver.get_quotes("XXX", "YYY", date(2026, 9, 4), 7, ["6E", "AI"])
    assert resolver.get_metrics_summary()["unresolved"] == 2

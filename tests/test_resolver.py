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
    """v1 default behavior: falls back entirely to SimulatedFareSource."""
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
    test_resolver_partial_carrier_merge()
    test_resolver_resilience_to_exceptions()
    test_resolver_full_primary_success()
    test_resolver_case_insensitive_carrier_matching()
    print("All FareResolver unit tests passed successfully!")

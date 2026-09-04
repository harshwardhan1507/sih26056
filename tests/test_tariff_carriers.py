"""
Unit tests for Air India and Akasa tariff sheet adapters (apix/collector/adapters/tariff_carriers.py).
"""

from datetime import date
from pathlib import Path
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from apix.collector.adapters.tariff_carriers import (
    AirIndiaTariffSheetSource,
    AkasaTariffSheetSource,
    parse_carrier_tariff_csv,
    AI_FIXTURE_CSV,
    QP_FIXTURE_CSV,
)
from apix.collector.resolver import FareResolver


def test_parse_air_india_fixture():
    bands = parse_carrier_tariff_csv(AI_FIXTURE_CSV, carrier_iata="AI")
    assert len(bands) >= 12
    for b in bands:
        assert "AI" in b.notes
        assert b.origin_iata
        assert b.destination_iata
        assert b.min_fare_inr is not None and b.min_fare_inr > 0
        assert b.max_fare_inr is not None and b.max_fare_inr >= b.min_fare_inr


def test_parse_akasa_fixture():
    bands = parse_carrier_tariff_csv(QP_FIXTURE_CSV, carrier_iata="QP")
    assert len(bands) >= 12
    for b in bands:
        assert "QP" in b.notes
        assert b.origin_iata
        assert b.destination_iata
        assert b.min_fare_inr is not None and b.min_fare_inr > 0
        assert b.max_fare_inr is not None and b.max_fare_inr >= b.min_fare_inr


def test_air_india_get_quotes():
    src = AirIndiaTariffSheetSource()
    quotes = src.get_quotes(
        origin="DEL",
        destination="BOM",
        as_of_date=date(2026, 9, 4),
        advance_window_days=7,
        carriers=["AI", "6E"],
    )
    assert len(quotes) == 1
    q = quotes[0]
    assert q.carrier_iata == "AI"
    assert q.source_id == "air_india_tariff_v1"
    assert q.collection_method == "tariff_sheet"
    assert q.total_fare_inr > 3000.0


def test_akasa_get_quotes():
    src = AkasaTariffSheetSource()
    quotes = src.get_quotes(
        origin="DEL",
        destination="BOM",
        as_of_date=date(2026, 9, 4),
        advance_window_days=7,
        carriers=["QP", "AI"],
    )
    assert len(quotes) == 1
    q = quotes[0]
    assert q.carrier_iata == "QP"
    assert q.source_id == "akasa_tariff_v1"
    assert q.collection_method == "tariff_sheet"
    assert q.total_fare_inr > 2000.0


def test_multi_carrier_resolver_chain():
    """Resolver querying IndiGo, Air India, and Akasa tariff sheet adapters sequentially."""
    ai_src = AirIndiaTariffSheetSource()
    qp_src = AkasaTariffSheetSource()
    resolver = FareResolver(primary_sources=[ai_src, qp_src])

    quotes = resolver.get_quotes(
        origin="DEL",
        destination="BOM",
        as_of_date=date(2026, 9, 4),
        advance_window_days=7,
        carriers=["AI", "QP", "SG"],
    )
    assert len(quotes) == 3
    by_carrier = {q.carrier_iata: q for q in quotes}

    assert by_carrier["AI"].source_id == "air_india_tariff_v1"
    assert by_carrier["AI"].collection_method == "tariff_sheet"

    assert by_carrier["QP"].source_id == "akasa_tariff_v1"
    assert by_carrier["QP"].collection_method == "tariff_sheet"

    # SG falls through to simulated fallback
    assert by_carrier["SG"].source_id == "simulated_v1"
    assert by_carrier["SG"].collection_method == "simulated"


if __name__ == "__main__":
    test_parse_air_india_fixture()
    test_parse_akasa_fixture()
    test_air_india_get_quotes()
    test_akasa_get_quotes()
    test_multi_carrier_resolver_chain()
    print("All additional carrier tariff sheet tests passed!")

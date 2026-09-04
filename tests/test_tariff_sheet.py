"""
Tests for the IndiGo tariff-sheet adapter (apix/collector/adapters/tariff_sheet.py).

All tests run against the pre-committed CSV fixture so no network access and
no pdfplumber memory issues are needed during CI.
"""

from datetime import date, datetime, timezone
from pathlib import Path
import math
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from apix.collector.adapters.tariff_sheet import (
    TariffBand,
    IndiGoTariffSheetSource,
    parse_indigo_tariff_csv,
    FIXTURE_CSV,
)
from apix.collector.adapters.base import FareQuote


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fixture_source() -> IndiGoTariffSheetSource:
    """Adapter pointed at the committed CSV fixture."""
    return IndiGoTariffSheetSource(use_fixture=True, fixture_csv=FIXTURE_CSV)


# ---------------------------------------------------------------------------
# CSV fixture parser tests
# ---------------------------------------------------------------------------

def test_parse_fixture_returns_bands():
    """Parsing the fixture CSV returns at least one TariffBand per basket route."""
    bands = parse_indigo_tariff_csv(FIXTURE_CSV, source_url=str(FIXTURE_CSV))
    assert len(bands) >= 12, f"Expected ≥12 bands, got {len(bands)}"


def test_band_fields_populated():
    """Every band in the fixture has required fields non-None."""
    bands = parse_indigo_tariff_csv(FIXTURE_CSV, source_url=str(FIXTURE_CSV))
    for band in bands:
        assert band.origin_iata, "origin_iata is empty"
        assert band.destination_iata, "destination_iata is empty"
        assert band.row_type in ("Maximum", "Minimum"), f"unexpected row_type: {band.row_type}"
        assert band.source_url, "source_url is empty"
        assert band.retrieved_at_utc is not None, "retrieved_at_utc is None"
        # min/max fares must be set (at least one non-NA fare per basket route)
        assert band.min_fare_inr is not None, f"min_fare_inr is None for {band.route_key} {band.row_type}"
        assert band.max_fare_inr is not None, f"max_fare_inr is None for {band.route_key} {band.row_type}"
        assert band.min_fare_inr > 0, f"min_fare_inr ≤ 0 for {band.route_key}"
        assert band.max_fare_inr >= band.min_fare_inr, (
            f"max < min for {band.route_key} {band.row_type}: "
            f"{band.max_fare_inr} < {band.min_fare_inr}"
        )


def test_basket_routes_all_present():
    """All 12 APIx basket routes appear in the fixture (in either direction)."""
    bands = parse_indigo_tariff_csv(FIXTURE_CSV, source_url=str(FIXTURE_CSV))
    route_pairs_in_fixture = {
        (b.origin_iata, b.destination_iata) for b in bands
    } | {
        (b.destination_iata, b.origin_iata) for b in bands
    }

    basket = [
        ("DEL", "BOM"), ("DEL", "BLR"), ("DEL", "CCU"),
        ("DEL", "MAA"), ("DEL", "HYD"), ("BOM", "BLR"),
        ("BOM", "MAA"), ("BOM", "CCU"), ("BLR", "HYD"),
        ("BLR", "MAA"), ("DEL", "GOI"), ("BOM", "GOI"),
    ]
    missing = [r for r in basket if r not in route_pairs_in_fixture]
    assert not missing, f"Basket routes missing from fixture: {missing}"


def test_effective_month_parsed():
    """Fixture CSV filename yields a parseable effective_month."""
    bands = parse_indigo_tariff_csv(FIXTURE_CSV, source_url=str(FIXTURE_CSV))
    # effective_month comes from FIXTURE_CSV path, which contains '2026-09-01'
    for band in bands:
        assert band.effective_month == "2026-09", (
            f"Expected effective_month='2026-09', got {band.effective_month!r}"
        )


# ---------------------------------------------------------------------------
# Adapter (FareSource) tests
# ---------------------------------------------------------------------------

def test_adapter_from_fixture_returns_fare_quotes():
    """Adapter returns FareQuote(s) for a known basket route."""
    src = _fixture_source()
    quotes = src.get_quotes(
        origin="DEL",
        destination="BOM",
        as_of_date=date(2026, 9, 4),
        advance_window_days=30,
        carriers=["6E", "AI", "SG"],
    )
    # Only IndiGo (6E) is served by this adapter
    assert len(quotes) == 1
    q = quotes[0]
    assert q.carrier_iata == "6E"
    assert q.collection_method == "tariff_sheet"
    assert q.source_id == "indigo_tariff_v1"
    assert q.quality_flag == "ok"
    assert q.origin_iata == "DEL"
    assert q.destination_iata == "BOM"
    assert q.total_fare_inr is not None and q.total_fare_inr > 0


def test_adapter_fare_is_midpoint():
    """The returned fare is the midpoint of the Minimum band's [min, max]."""
    src = _fixture_source()
    bands = parse_indigo_tariff_csv(FIXTURE_CSV, source_url=str(FIXTURE_CSV))

    # Find the Minimum band for DEL-BOM (or BOM-DEL)
    min_band = next(
        (b for b in bands
         if b.row_type == "Minimum"
         and {b.origin_iata, b.destination_iata} == {"DEL", "BOM"}),
        None,
    )
    assert min_band is not None, "DEL-BOM Minimum band not found in fixture"

    expected_midpoint = round((min_band.min_fare_inr + min_band.max_fare_inr) / 2.0, 2)

    quotes = src.get_quotes("DEL", "BOM", date(2026, 9, 4), 30, ["6E"])
    assert len(quotes) == 1
    assert math.isclose(quotes[0].total_fare_inr, expected_midpoint, rel_tol=1e-4), (
        f"Expected midpoint {expected_midpoint}, got {quotes[0].total_fare_inr}"
    )


def test_adapter_reverse_direction_works():
    """Adapter serves the reverse direction of a basket route."""
    src = _fixture_source()
    quotes = src.get_quotes("BOM", "DEL", date(2026, 9, 4), 7, ["6E"])
    assert len(quotes) == 1
    assert quotes[0].origin_iata == "BOM"
    assert quotes[0].destination_iata == "DEL"


def test_adapter_non_indigo_carrier_returns_empty():
    """Adapter returns [] when IndiGo (6E) is not in the carriers list."""
    src = _fixture_source()
    quotes = src.get_quotes("DEL", "BOM", date(2026, 9, 4), 30, ["AI", "SG"])
    assert quotes == [], f"Expected [], got {quotes}"


def test_adapter_unknown_route_returns_empty():
    """Adapter returns [] for a route not in the tariff sheet."""
    src = _fixture_source()
    quotes = src.get_quotes("DEL", "JFK", date(2026, 9, 4), 30, ["6E"])
    assert quotes == [], f"Expected [] for unknown route, got {quotes}"


def test_adapter_parse_failure_returns_empty():
    """If the fixture CSV doesn't exist, adapter returns [] without raising."""
    src = IndiGoTariffSheetSource(
        use_fixture=True,
        fixture_csv=Path("nonexistent_fixture_that_does_not_exist.csv"),
    )
    quotes = src.get_quotes("DEL", "BOM", date(2026, 9, 4), 30, ["6E"])
    assert quotes == [], (
        "Adapter must return [] (not raise) when fixture is missing"
    )


def test_fare_quote_fields_complete():
    """All FareQuote fields required by downstream code are populated."""
    src = _fixture_source()
    quotes = src.get_quotes("BOM", "BLR", date(2026, 9, 4), 15, ["6E"])
    assert len(quotes) == 1
    q = quotes[0]
    assert isinstance(q, FareQuote)
    assert isinstance(q.collected_at_utc, datetime)
    assert isinstance(q.departure_date, date)
    assert isinstance(q.advance_window_days, int)
    assert q.fare_class == "Economy"
    assert q.total_fare_inr is not None


# ---------------------------------------------------------------------------
# __main__ runner
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    test_parse_fixture_returns_bands()
    test_band_fields_populated()
    test_basket_routes_all_present()
    test_effective_month_parsed()
    test_adapter_from_fixture_returns_fare_quotes()
    test_adapter_fare_is_midpoint()
    test_adapter_reverse_direction_works()
    test_adapter_non_indigo_carrier_returns_empty()
    test_adapter_unknown_route_returns_empty()
    test_adapter_parse_failure_returns_empty()
    test_fare_quote_fields_complete()
    print("All tariff-sheet tests passed!")

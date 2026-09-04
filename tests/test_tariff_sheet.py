"""
Tests for the IndiGo tariff-sheet adapter (apix/collector/adapters/tariff_sheet.py).

All tests run against the pre-committed CSV fixture so no network access and
no pdfplumber memory issues are needed during CI.
"""

from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import math
import sys

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from apix.collector.adapters.tariff_sheet import (
    bucket_for_window,
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


def test_adapter_fare_is_bucket_midpoint():
    """
    The returned fare is the midpoint of the Minimum-row and Maximum-row
    fares AT THE BUCKET selected for the requested advance window.

    Previously this adapter used the Minimum row's overall [min, max]
    midpoint while the Air India / Akasa adapters used the Maximum row's
    midpoint, so carriers sat on different price definitions inside the same
    matched sample.
    """
    src = _fixture_source()
    bands = parse_indigo_tariff_csv(FIXTURE_CSV, source_url=str(FIXTURE_CSV))

    window = 30
    idx = bucket_for_window(window) - 1

    def _row(row_type):
        return next(
            (b for b in bands
             if b.row_type == row_type
             and {b.origin_iata, b.destination_iata} == {"DEL", "BOM"}),
            None,
        )

    min_band, max_band = _row("Minimum"), _row("Maximum")
    assert min_band is not None and max_band is not None, "DEL-BOM bands not in fixture"

    expected = round((min_band.fares[idx] + max_band.fares[idx]) / 2.0, 2)

    quotes = src.get_quotes("DEL", "BOM", date(2026, 9, 4), window, ["6E"])
    assert len(quotes) == 1
    assert math.isclose(quotes[0].total_fare_inr, expected, rel_tol=1e-4), (
        f"Expected bucket-{idx + 1} midpoint {expected}, got {quotes[0].total_fare_inr}"
    )


def test_adapter_fare_varies_by_advance_window():
    """
    A tariff quote must respond to the advance window.

    All five windows used to return one identical number, so 6E contributed a
    price relative of exactly 1.0 every day while still occupying a slot in
    the matched sample and damping the index.
    """
    src = _fixture_source()
    fares = [
        src.get_quotes("DEL", "BOM", date(2026, 9, 4), w, ["6E"])[0].total_fare_inr
        for w in (45, 30, 15, 7, 1)
    ]

    assert len(set(fares)) == len(fares), f"Windows returned duplicate fares: {fares}"
    assert fares == sorted(fares), (
        f"Fares must rise as departure approaches (T+45 -> T+1); got {fares}"
    )


def test_adapter_departure_date_reflects_advance_window():
    """The flight quoted today departs advance_window_days later, not today."""
    src = _fixture_source()
    as_of = date(2026, 9, 4)
    for window in (1, 7, 15, 30, 45):
        quote = src.get_quotes("DEL", "BOM", as_of, window, ["6E"])[0]
        assert quote.departure_date == as_of + timedelta(days=window), (
            f"T+{window} quote departs {quote.departure_date}, expected "
            f"{as_of + timedelta(days=window)}"
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

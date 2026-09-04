"""
Unit tests for the Kaggle historical panel real-data loader and adapter.
"""

from datetime import date
from io import StringIO
from pathlib import Path
import sys

# Ensure root directory is on sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from apix.collector.adapters.base import FareQuote
from apix.collector.adapters.kaggle import (
    KaggleFlightRecord,
    KaggleDatasetLoader,
    KaggleFareSource,
    normalize_airline,
    normalize_city,
    normalize_class,
    normalize_flight_number,
    map_days_left_to_window,
    window_to_tag,
    tag_to_window,
    APIX_ADVANCE_WINDOWS,
    CITY_TO_IATA,
    AIRLINE_TO_IATA,
)
from apix.index.elementary import build_elementary_index

FIXTURE_PATH = ROOT_DIR / "tests" / "fixtures" / "sample_clean_dataset.csv"


# --- Normalization Unit Tests ---

def test_normalize_airline():
    assert normalize_airline("Indigo") == ("IndiGo", "6E")
    assert normalize_airline("indigo") == ("IndiGo", "6E")
    assert normalize_airline("6e") == ("IndiGo", "6E")
    assert normalize_airline("Air India") == ("Air India", "AI")
    assert normalize_airline("air_india") == ("Air India", "AI")
    assert normalize_airline("Vistara") == ("Vistara", "UK")
    assert normalize_airline("SpiceJet") == ("SpiceJet", "SG")
    assert normalize_airline("AirAsia") == ("AirAsia", "I5")
    assert normalize_airline("AirAsia India") == ("AirAsia", "I5")
    assert normalize_airline("GO FIRST") == ("GO FIRST", "G8")
    assert normalize_airline("GoAir") == ("GO FIRST", "G8")
    assert normalize_airline("Akasa Air") == ("Akasa Air", "QP")

    try:
        normalize_airline("PanAm")
        assert False, "Expected ValueError for PanAm"
    except ValueError:
        pass


def test_normalize_city():
    assert normalize_city("Delhi") == ("Delhi", "DEL")
    assert normalize_city("New Delhi") == ("Delhi", "DEL")
    assert normalize_city("DEL") == ("Delhi", "DEL")
    assert normalize_city("Mumbai") == ("Mumbai", "BOM")
    assert normalize_city("Bombay") == ("Mumbai", "BOM")
    assert normalize_city("Bangalore") == ("Bangalore", "BLR")
    assert normalize_city("Bengaluru") == ("Bangalore", "BLR")
    assert normalize_city("Kolkata") == ("Kolkata", "CCU")
    assert normalize_city("Calcutta") == ("Kolkata", "CCU")
    assert normalize_city("Hyderabad") == ("Hyderabad", "HYD")
    assert normalize_city("Chennai") == ("Chennai", "MAA")
    assert normalize_city("Madras") == ("Chennai", "MAA")

    try:
        normalize_city("Atlantis")
        assert False, "Expected ValueError for Atlantis"
    except ValueError:
        pass


def test_normalize_class():
    assert normalize_class("Economy") == "Economy"
    assert normalize_class("economy") == "Economy"
    assert normalize_class("Business") == "Business"
    assert normalize_class("business") == "Business"
    assert normalize_class("Premium Economy") == "Premium"


def test_normalize_flight_number():
    assert normalize_flight_number("SG-8709") == "SG-8709"
    assert normalize_flight_number("6E 2053") == "6E-2053"
    assert normalize_flight_number("6e-2053") == "6E-2053"
    assert normalize_flight_number("8709", carrier_iata="SG") == "SG-8709"


# --- Advance Purchase Window Mapping Tests ---

def test_map_days_left_exact():
    # Only exact values in (1, 7, 15, 30, 45) should map
    assert map_days_left_to_window(1, strategy="exact") == 1
    assert map_days_left_to_window(7, strategy="exact") == 7
    assert map_days_left_to_window(15, strategy="exact") == 15
    assert map_days_left_to_window(30, strategy="exact") == 30
    assert map_days_left_to_window(45, strategy="exact") == 45

    # Intermediate / invalid values should return None
    assert map_days_left_to_window(2, strategy="exact") is None
    assert map_days_left_to_window(8, strategy="exact") is None
    assert map_days_left_to_window(14, strategy="exact") is None
    assert map_days_left_to_window(28, strategy="exact") is None
    assert map_days_left_to_window(42, strategy="exact") is None
    assert map_days_left_to_window(0, strategy="exact") is None
    assert map_days_left_to_window(-5, strategy="exact") is None


def test_map_days_left_nearest():
    # Nearest anchor mapping
    assert map_days_left_to_window(1, strategy="nearest") == 1
    assert map_days_left_to_window(2, strategy="nearest") == 1
    assert map_days_left_to_window(3, strategy="nearest") == 1
    assert map_days_left_to_window(4, strategy="nearest") == 1  # 4 is equidistant from 1 and 7, min() selects 1
    assert map_days_left_to_window(5, strategy="nearest") == 7
    assert map_days_left_to_window(6, strategy="nearest") == 7
    assert map_days_left_to_window(8, strategy="nearest") == 7
    assert map_days_left_to_window(11, strategy="nearest") == 7  # 11 is equidistant from 7 and 15
    assert map_days_left_to_window(12, strategy="nearest") == 15
    assert map_days_left_to_window(14, strategy="nearest") == 15
    assert map_days_left_to_window(22, strategy="nearest") == 15
    assert map_days_left_to_window(23, strategy="nearest") == 30
    assert map_days_left_to_window(28, strategy="nearest") == 30
    assert map_days_left_to_window(37, strategy="nearest") == 30
    assert map_days_left_to_window(38, strategy="nearest") == 45
    assert map_days_left_to_window(42, strategy="nearest") == 45
    assert map_days_left_to_window(49, strategy="nearest") == 45


def test_map_days_left_bucket():
    # Statistical intervals
    # 1: [1, 3]
    assert map_days_left_to_window(1, strategy="bucket") == 1
    assert map_days_left_to_window(3, strategy="bucket") == 1
    # 7: [4, 10]
    assert map_days_left_to_window(4, strategy="bucket") == 7
    assert map_days_left_to_window(7, strategy="bucket") == 7
    assert map_days_left_to_window(10, strategy="bucket") == 7
    # 15: [11, 22]
    assert map_days_left_to_window(11, strategy="bucket") == 15
    assert map_days_left_to_window(15, strategy="bucket") == 15
    assert map_days_left_to_window(22, strategy="bucket") == 15
    # 30: [23, 37]
    assert map_days_left_to_window(23, strategy="bucket") == 30
    assert map_days_left_to_window(30, strategy="bucket") == 30
    assert map_days_left_to_window(37, strategy="bucket") == 30
    # 45: [38, inf)
    assert map_days_left_to_window(38, strategy="bucket") == 45
    assert map_days_left_to_window(45, strategy="bucket") == 45
    assert map_days_left_to_window(50, strategy="bucket") == 45


def test_window_tags():
    assert window_to_tag(1) == "T+1"
    assert window_to_tag(7) == "T+7"
    assert window_to_tag(15) == "T+15"
    assert window_to_tag(30) == "T+30"
    assert window_to_tag(45) == "T+45"

    assert tag_to_window("T+1") == 1
    assert tag_to_window("T+7") == 7
    assert tag_to_window("T+15") == 15
    assert tag_to_window("T+30") == 30
    assert tag_to_window("T+45") == 45
    assert tag_to_window("15") == 15


# --- Dataset Loader Tests ---

def test_load_records_exact_strategy():
    records = KaggleDatasetLoader.load_records(FIXTURE_PATH, window_strategy="exact")
    assert len(records) > 0

    for rec in records:
        assert rec.advance_window_days in APIX_ADVANCE_WINDOWS
        assert rec.advance_window_tag == f"T+{rec.advance_window_days}"
        assert rec.origin_iata in CITY_TO_IATA.values()
        assert rec.destination_iata in CITY_TO_IATA.values()
        assert rec.carrier_iata in [m[1] for m in AIRLINE_TO_IATA.values()]
        assert rec.price_inr > 0
        assert rec.duration_hours > 0
        assert rec.fare_class in ("Economy", "Business", "Premium")


def test_load_records_nearest_and_bucket():
    records_exact = KaggleDatasetLoader.load_records(FIXTURE_PATH, window_strategy="exact")
    records_nearest = KaggleDatasetLoader.load_records(FIXTURE_PATH, window_strategy="nearest")
    records_bucket = KaggleDatasetLoader.load_records(FIXTURE_PATH, window_strategy="bucket")

    # The fixture contains 5 rows with intermediate days (2, 8, 14, 28, 42)
    # Nearest and bucket should load all rows while exact filters intermediate days
    assert len(records_nearest) > len(records_exact)
    assert len(records_bucket) > len(records_exact)
    assert len(records_nearest) == len(records_bucket)


def test_stream_filter_by_class_and_route():
    # Stream only Economy for DEL -> BOM
    economy_records = list(KaggleDatasetLoader.stream_records(
        FIXTURE_PATH,
        window_strategy="exact",
        fare_class="Economy",
        origin_iata="DEL",
        destination_iata="BOM",
    ))
    assert len(economy_records) > 0
    assert all(r.fare_class == "Economy" for r in economy_records)
    assert all(r.origin_iata == "DEL" and r.destination_iata == "BOM" for r in economy_records)

    # Stream only Business
    business_records = list(KaggleDatasetLoader.stream_records(
        FIXTURE_PATH,
        window_strategy="exact",
        fare_class="Business",
    ))
    assert len(business_records) > 0
    assert all(r.fare_class == "Business" for r in business_records)


# --- FareQuote Conversion & Compatibility Tests ---

def test_to_fare_quote_conversion():
    records = KaggleDatasetLoader.load_records(FIXTURE_PATH, window_strategy="exact")
    rec = records[0]

    fq = rec.to_fare_quote(as_of_date=date(2026, 1, 1))
    assert isinstance(fq, FareQuote)
    assert fq.origin_iata == rec.origin_iata
    assert fq.destination_iata == rec.destination_iata
    assert fq.carrier_iata == rec.carrier_iata
    assert fq.advance_window_days == rec.advance_window_days
    assert fq.fare_class == rec.fare_class
    assert fq.total_fare_inr == rec.price_inr
    assert fq.source_id == "kaggle_easemytrip_v1"
    assert fq.collection_method == "scrape"
    assert fq.quality_flag == "ok"

    row = rec.to_row()
    assert "flight_number" in row
    assert "duration_hours" in row
    assert "days_left" in row
    assert "advance_window_tag" in row
    assert row["origin_iata"] == rec.origin_iata


# --- KaggleFareSource Adapter & Pipeline Tests ---

def test_kaggle_fare_source_get_quotes():
    source = KaggleFareSource(
        records_or_source=FIXTURE_PATH,
        window_strategy="exact",
        fare_class="Economy",
        price_agg="min",
    )

    # Test DEL -> BOM at T+7
    quotes = source.get_quotes(
        origin="DEL",
        destination="BOM",
        as_of_date=date(2026, 1, 1),
        advance_window_days=7,
        carriers=["6E", "AI", "SG", "UK", "G8", "I5"],
    )

    assert len(quotes) > 0
    carriers_returned = {q.carrier_iata for q in quotes}
    # All 6 carriers are present at T+7 in the sample fixture
    assert "6E" in carriers_returned
    assert "AI" in carriers_returned
    assert "SG" in carriers_returned
    assert "UK" in carriers_returned

    for q in quotes:
        assert isinstance(q, FareQuote)
        assert q.origin_iata == "DEL"
        assert q.destination_iata == "BOM"
        assert q.advance_window_days == 7
        assert q.total_fare_inr is not None
        assert q.total_fare_inr > 0
        assert q.source_id == "kaggle_easemytrip_v1"
        assert q.collection_method == "scrape"


def test_kaggle_daily_prices_to_elementary_index():
    records = KaggleDatasetLoader.load_records(FIXTURE_PATH, window_strategy="nearest")
    # Generate daily price series for DEL-BOM at T+7
    daily_prices = KaggleDatasetLoader.to_daily_carrier_prices(
        records,
        origin_iata="DEL",
        destination_iata="BOM",
        window_days=7,
        fare_class="Economy",
        agg_func="min",
    )
    assert len(daily_prices) > 0
    # Feed real Kaggle prices into Jevons elementary index
    index_series = build_elementary_index(daily_prices, base_value=100.0)
    assert len(index_series) == len(daily_prices)
    assert index_series[0] == 100.0
    for val in index_series:
        assert val > 0.0


# --- Edge Cases & Malformed Row Handling ---

def test_corrupted_rows_handling():
    corrupted_csv = """Unnamed: 0,airline,flight,source_city,departure_time,stops,arrival_time,destination_city,class,duration,days_left,price
0,UnknownAirlines,XX-123,Delhi,Morning,zero,Afternoon,Mumbai,Economy,2.0,1,5000
1,Indigo,6E-100,UnknownCity,Morning,zero,Afternoon,Mumbai,Economy,2.0,1,5000
2,Indigo,6E-101,Delhi,Morning,zero,Afternoon,Mumbai,Economy,-1.0,1,5000
3,Indigo,6E-102,Delhi,Morning,zero,Afternoon,Mumbai,Economy,2.0,1,-100
4,Indigo,6E-103,Delhi,Morning,zero,Afternoon,Mumbai,Economy,2.0,2,5000
5,Indigo,6E-104,Delhi,Morning,zero,Afternoon,Mumbai,Economy,2.0,7,5000
"""
    records = KaggleDatasetLoader.load_records(StringIO(corrupted_csv), window_strategy="exact")
    # Only row 5 is valid with an exact window (days_left=7)
    assert len(records) == 1
    assert records[0].flight_number == "6E-104"
    assert records[0].price_inr == 5000.0


if __name__ == "__main__":
    test_normalize_airline()
    test_normalize_city()
    test_normalize_class()
    test_normalize_flight_number()
    test_map_days_left_exact()
    test_map_days_left_nearest()
    test_map_days_left_bucket()
    test_window_tags()
    test_load_records_exact_strategy()
    test_load_records_nearest_and_bucket()
    test_stream_filter_by_class_and_route()
    test_to_fare_quote_conversion()
    test_kaggle_fare_source_get_quotes()
    test_kaggle_daily_prices_to_elementary_index()
    test_corrupted_rows_handling()
    print("All Kaggle loader unit tests passed successfully!")

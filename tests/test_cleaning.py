"""
Comprehensive unit tests for APIx data cleaning pipeline (Issue #9).

Validates:
  - Schema validation, type checks, and CPI Golden Rule (sold-out is missing, never zero)
  - Multi-source deduplication with deterministic source tier and recency precedence
  - Log-transformed Tukey IQR and MAD outlier detection (zero dispersion, small samples, right-skew)
  - Missing price & sold-out flight imputation with strict provenance tracking
  - End-to-end CleaningPipeline execution and audit reporting
  - Seamless integration with elementary Jevons index (matched-sample drops)
  - Real-world validation against Kaggle EaseMyTrip sample dataset
"""

from datetime import date, datetime, timedelta, timezone
from pathlib import Path
import sys

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from apix.collector.adapters.base import FareQuote
from apix.collector.adapters.kaggle import KaggleDatasetLoader
from apix.cleaning import (
    CleaningPipeline,
    CleaningReport,
    clean_quote_dict,
    deduplicate_quotes,
    detect_outliers,
    impute_missing_quotes,
    validate_fare_quote,
)
from apix.index.elementary import build_elementary_index

FIXTURE_PATH = ROOT_DIR / "tests" / "fixtures" / "sample_clean_dataset.csv"


# ---------------------------------------------------------------------------
# 1. Schema & CPI Domain Constraints Tests
# ---------------------------------------------------------------------------

def test_schema_valid_quote():
    q = FareQuote(
        collected_at_utc=datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc),
        departure_date=date(2026, 9, 8),
        advance_window_days=7,
        origin_iata="DEL",
        destination_iata="BOM",
        carrier_iata="6E",
        fare_class="Economy",
        total_fare_inr=5400.0,
        source_id="tripjack_v1",
        collection_method="api",
        quality_flag="ok",
    )
    res = validate_fare_quote(q)
    assert res.is_valid is True
    assert len(res.errors) == 0


def test_schema_reject_zero_and_negative_fares():
    # In CPI, zero fares or negative fares are data errors
    for bad_price in (0.0, -150.0):
        q = FareQuote(
            collected_at_utc=datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc),
            departure_date=date(2026, 9, 8),
            advance_window_days=7,
            origin_iata="DEL",
            destination_iata="BOM",
            carrier_iata="6E",
            fare_class="Economy",
            total_fare_inr=bad_price,
            source_id="test",
            collection_method="scrape",
            quality_flag="ok",
        )
        res = validate_fare_quote(q)
        assert res.is_valid is False
        assert any("positive" in err for err in res.errors)


def test_schema_sold_out_consistency():
    # Case 1: Sold-out must have total_fare_inr = None
    q_conflict = FareQuote(
        collected_at_utc=datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc),
        departure_date=date(2026, 9, 8),
        advance_window_days=7,
        origin_iata="DEL",
        destination_iata="BOM",
        carrier_iata="AI",
        fare_class="Economy",
        total_fare_inr=4500.0,  # Conflict: price present but flagged sold_out
        source_id="test",
        collection_method="scrape",
        quality_flag="sold_out",
    )
    res1 = validate_fare_quote(q_conflict)
    assert res1.is_valid is False

    # Case 2: None fare with quality_flag='ok' is invalid
    q_none_ok = FareQuote(
        collected_at_utc=datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc),
        departure_date=date(2026, 9, 8),
        advance_window_days=7,
        origin_iata="DEL",
        destination_iata="BOM",
        carrier_iata="AI",
        fare_class="Economy",
        total_fare_inr=None,
        source_id="test",
        collection_method="scrape",
        quality_flag="ok",
    )
    res2 = validate_fare_quote(q_none_ok)
    assert res2.is_valid is False

    # Case 3: Proper sold-out quote passes
    q_proper_sold_out = FareQuote(
        collected_at_utc=datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc),
        departure_date=date(2026, 9, 8),
        advance_window_days=7,
        origin_iata="DEL",
        destination_iata="BOM",
        carrier_iata="AI",
        fare_class="Economy",
        total_fare_inr=None,
        source_id="test",
        collection_method="scrape",
        quality_flag="sold_out",
    )
    assert validate_fare_quote(q_proper_sold_out).is_valid is True


def test_schema_invalid_iata_and_route():
    # Same origin and destination
    q_same = FareQuote(
        collected_at_utc=datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc),
        departure_date=date(2026, 9, 8),
        advance_window_days=7,
        origin_iata="DEL",
        destination_iata="DEL",
        carrier_iata="6E",
        fare_class="Economy",
        total_fare_inr=5000.0,
        source_id="test",
        collection_method="api",
        quality_flag="ok",
    )
    res = validate_fare_quote(q_same)
    assert res.is_valid is False
    assert any("identical" in err for err in res.errors)

    # Invalid IATA code length
    q_bad_iata = FareQuote(
        collected_at_utc=datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc),
        departure_date=date(2026, 9, 8),
        advance_window_days=7,
        origin_iata="DELHI",
        destination_iata="BOM",
        carrier_iata="6E",
        fare_class="Economy",
        total_fare_inr=5000.0,
        source_id="test",
        collection_method="api",
        quality_flag="ok",
    )
    assert validate_fare_quote(q_bad_iata).is_valid is False


def test_clean_quote_dict_auto_repair():
    raw = {
        "collected_at_utc": "2026-09-01T12:00:00+00:00",
        "departure_date": "2026-09-08",
        "advance_window_days": "7",
        "origin_iata": "del",
        "destination_iata": "bom",
        "carrier_iata": "6e",
        "fare_class": "economy",
        "total_fare_inr": None,
        "source_id": "test_raw",
        "collection_method": "scrape",
        "quality_flag": "ok",  # will auto-repair to sold_out
    }
    q, errors = clean_quote_dict(raw, auto_repair_sold_out=True)
    assert len(errors) == 0
    assert q is not None
    assert q.origin_iata == "DEL"
    assert q.carrier_iata == "6E"
    assert q.quality_flag == "sold_out"
    assert q.total_fare_inr is None


# ---------------------------------------------------------------------------
# 2. Deduplication Tests
# ---------------------------------------------------------------------------

def test_deduplication_prefers_api_over_scrape():
    dep = date(2026, 9, 8)
    # Quote from scrape
    q_scrape = FareQuote(
        collected_at_utc=datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc),
        departure_date=dep,
        advance_window_days=7,
        origin_iata="DEL",
        destination_iata="BOM",
        carrier_iata="6E",
        fare_class="Economy",
        total_fare_inr=5250.0,
        source_id="scraper_v1",
        collection_method="scrape",
        quality_flag="ok",
    )
    # Quote from API
    q_api = FareQuote(
        collected_at_utc=datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc),
        departure_date=dep,
        advance_window_days=7,
        origin_iata="DEL",
        destination_iata="BOM",
        carrier_iata="6E",
        fare_class="Economy",
        total_fare_inr=5200.0,
        source_id="tripjack_v1",
        collection_method="api",
        quality_flag="ok",
    )
    unique, dropped = deduplicate_quotes([q_scrape, q_api])
    assert len(unique) == 1
    assert dropped == 1
    assert unique[0].collection_method == "api"
    assert unique[0].total_fare_inr == 5200.0


def test_deduplication_prefers_latest_timestamp():
    dep = date(2026, 9, 8)
    q_early = FareQuote(
        collected_at_utc=datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc),
        departure_date=dep,
        advance_window_days=7,
        origin_iata="DEL",
        destination_iata="BOM",
        carrier_iata="AI",
        fare_class="Economy",
        total_fare_inr=6000.0,
        source_id="test",
        collection_method="scrape",
        quality_flag="ok",
    )
    q_later = FareQuote(
        collected_at_utc=datetime(2026, 9, 1, 11, 0, tzinfo=timezone.utc),
        departure_date=dep,
        advance_window_days=7,
        origin_iata="DEL",
        destination_iata="BOM",
        carrier_iata="AI",
        fare_class="Economy",
        total_fare_inr=6300.0,
        source_id="test",
        collection_method="scrape",
        quality_flag="ok",
    )
    unique, dropped = deduplicate_quotes([q_early, q_later])
    assert len(unique) == 1
    assert dropped == 1
    assert unique[0].total_fare_inr == 6300.0


# ---------------------------------------------------------------------------
# 3. Outlier Detection Tests
# ---------------------------------------------------------------------------

def test_outlier_detection_log_tukey():
    dep = date(2026, 9, 8)
    carriers = ["6E", "AI", "QP", "SG", "IX", "UK", "G8", "I5"]
    normal_prices = [5000.0, 5200.0, 5400.0, 5600.0, 5800.0, 6000.0]
    quotes = [
        FareQuote(
            collected_at_utc=datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc),
            departure_date=dep,
            advance_window_days=7,
            origin_iata="DEL",
            destination_iata="BOM",
            carrier_iata=carriers[i],
            fare_class="Economy",
            total_fare_inr=normal_prices[i],
            source_id="test",
            collection_method="api",
            quality_flag="ok",
        )
        for i in range(6)
    ]
    # Add an extreme upper spike (₹500,000 placeholder/currency error)
    quotes.append(FareQuote(
        collected_at_utc=datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc),
        departure_date=dep,
        advance_window_days=7,
        origin_iata="DEL",
        destination_iata="BOM",
        carrier_iata="UK",
        fare_class="Economy",
        total_fare_inr=500000.0,
        source_id="test",
        collection_method="api",
        quality_flag="ok",
    ))
    # Add an extreme lower drop (₹10 data entry error)
    quotes.append(FareQuote(
        collected_at_utc=datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc),
        departure_date=dep,
        advance_window_days=7,
        origin_iata="DEL",
        destination_iata="BOM",
        carrier_iata="I5",
        fare_class="Economy",
        total_fare_inr=10.0,
        source_id="test",
        collection_method="api",
        quality_flag="ok",
    ))

    flagged_quotes, outlier_count = detect_outliers(quotes, method="tukey", k=2.0)
    assert outlier_count == 2

    flagged_carriers = {q.carrier_iata for q in flagged_quotes if q.quality_flag == "outlier"}
    assert "UK" in flagged_carriers  # 500k
    assert "I5" in flagged_carriers  # 10


def test_outlier_detection_zero_dispersion():
    dep = date(2026, 9, 8)
    carriers = ["6E", "AI", "QP", "SG", "IX"]
    # All carriers priced identically at ₹4,999 (zero dispersion)
    quotes = [
        FareQuote(
            collected_at_utc=datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc),
            departure_date=dep,
            advance_window_days=7,
            origin_iata="DEL",
            destination_iata="BOM",
            carrier_iata=c,
            fare_class="Economy",
            total_fare_inr=4999.0,
            source_id="test",
            collection_method="api",
            quality_flag="ok",
        )
        for c in carriers
    ]
    flagged, count = detect_outliers(quotes, method="tukey")
    assert count == 0
    assert all(q.quality_flag == "ok" for q in flagged)


def test_outlier_detection_small_sample():
    dep = date(2026, 9, 8)
    # Only 2 carriers (duopoly) -> N < 4 bypasses outlier detection
    quotes = [
        FareQuote(
            collected_at_utc=datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc),
            departure_date=dep,
            advance_window_days=7,
            origin_iata="DEL",
            destination_iata="BOM",
            carrier_iata="6E",
            fare_class="Economy",
            total_fare_inr=4000.0,
            source_id="test",
            collection_method="api",
            quality_flag="ok",
        ),
        FareQuote(
            collected_at_utc=datetime(2026, 9, 1, 10, 0, tzinfo=timezone.utc),
            departure_date=dep,
            advance_window_days=7,
            origin_iata="DEL",
            destination_iata="BOM",
            carrier_iata="AI",
            fare_class="Economy",
            total_fare_inr=150000.0,  # extreme, but N=2
            source_id="test",
            collection_method="api",
            quality_flag="ok",
        ),
    ]
    flagged, count = detect_outliers(quotes, min_sample_size=4)
    assert count == 0
    assert all(q.quality_flag == "ok" for q in flagged)


# ---------------------------------------------------------------------------
# 4. Imputation Tests
# ---------------------------------------------------------------------------

def test_imputation_class_mean_and_provenance():
    day1 = date(2026, 9, 1)
    day2 = date(2026, 9, 2)

    # Day 1: 6E = 4000, AI = 5000
    # Day 2: 6E = 4400 (+10%), AI = sold_out
    q_d1_6e = FareQuote(
        collected_at_utc=datetime(2026, 8, 25, 10, 0, tzinfo=timezone.utc),
        departure_date=day1,
        advance_window_days=7,
        origin_iata="DEL",
        destination_iata="BOM",
        carrier_iata="6E",
        fare_class="Economy",
        total_fare_inr=4000.0,
        source_id="test",
        collection_method="api",
        quality_flag="ok",
    )
    q_d1_ai = FareQuote(
        collected_at_utc=datetime(2026, 8, 25, 10, 0, tzinfo=timezone.utc),
        departure_date=day1,
        advance_window_days=7,
        origin_iata="DEL",
        destination_iata="BOM",
        carrier_iata="AI",
        fare_class="Economy",
        total_fare_inr=5000.0,
        source_id="test",
        collection_method="api",
        quality_flag="ok",
    )
    q_d2_6e = FareQuote(
        collected_at_utc=datetime(2026, 8, 26, 10, 0, tzinfo=timezone.utc),
        departure_date=day2,
        advance_window_days=7,
        origin_iata="DEL",
        destination_iata="BOM",
        carrier_iata="6E",
        fare_class="Economy",
        total_fare_inr=4400.0,
        source_id="test",
        collection_method="api",
        quality_flag="ok",
    )
    q_d2_ai = FareQuote(
        collected_at_utc=datetime(2026, 8, 26, 10, 0, tzinfo=timezone.utc),
        departure_date=day2,
        advance_window_days=7,
        origin_iata="DEL",
        destination_iata="BOM",
        carrier_iata="AI",
        fare_class="Economy",
        total_fare_inr=None,
        source_id="test",
        collection_method="scrape",
        quality_flag="sold_out",
    )

    imputed_quotes, count = impute_missing_quotes([q_d1_6e, q_d1_ai, q_d2_6e, q_d2_ai], strategy="class_mean")
    assert count == 1

    # Find the imputed quote for Day 2 AI
    ai_d2 = next(q for q in imputed_quotes if q.departure_date == day2 and q.carrier_iata == "AI")
    assert ai_d2.collection_method == "imputed"
    assert ai_d2.quality_flag == "imputed"
    # Imputed price = 5000 * (4400/4000) = 5500.0
    assert ai_d2.total_fare_inr == 5500.0


# ---------------------------------------------------------------------------
# 5. CleaningPipeline End-to-End Tests
# ---------------------------------------------------------------------------

def test_pipeline_end_to_end():
    pipeline = CleaningPipeline(
        deduplicate=True,
        detect_outliers=True,
        impute_missing=False,
    )

    # Mix of valid, duplicate, invalid, and sold-out quotes
    raw_dicts = [
        # Valid quote 1
        {
            "collected_at_utc": "2026-09-01T10:00:00+00:00",
            "departure_date": "2026-09-08",
            "advance_window_days": 7,
            "origin_iata": "DEL",
            "destination_iata": "BOM",
            "carrier_iata": "6E",
            "fare_class": "Economy",
            "total_fare_inr": 5000.0,
            "source_id": "test_api",
            "collection_method": "api",
            "quality_flag": "ok",
        },
        # Duplicate quote 1 from scrape (should be dropped)
        {
            "collected_at_utc": "2026-09-01T10:05:00+00:00",
            "departure_date": "2026-09-08",
            "advance_window_days": 7,
            "origin_iata": "DEL",
            "destination_iata": "BOM",
            "carrier_iata": "6E",
            "fare_class": "Economy",
            "total_fare_inr": 5050.0,
            "source_id": "test_scrape",
            "collection_method": "scrape",
            "quality_flag": "ok",
        },
        # Corrupt quote with zero fare (should be rejected in validation)
        {
            "collected_at_utc": "2026-09-01T10:00:00+00:00",
            "departure_date": "2026-09-08",
            "advance_window_days": 7,
            "origin_iata": "DEL",
            "destination_iata": "BOM",
            "carrier_iata": "QP",
            "fare_class": "Economy",
            "total_fare_inr": 0.0,
            "source_id": "test_corrupt",
            "collection_method": "api",
            "quality_flag": "ok",
        },
        # Sold-out quote
        {
            "collected_at_utc": "2026-09-01T10:00:00+00:00",
            "departure_date": "2026-09-08",
            "advance_window_days": 7,
            "origin_iata": "DEL",
            "destination_iata": "BOM",
            "carrier_iata": "SG",
            "fare_class": "Economy",
            "total_fare_inr": None,
            "source_id": "test_api",
            "collection_method": "api",
            "quality_flag": "sold_out",
        },
    ]

    clean_quotes, report = pipeline.clean_quotes(raw_dicts)
    assert report.total_input == 4
    assert report.valid_count == 3
    assert report.invalid_count == 1
    assert report.duplicates_dropped == 1
    assert report.sold_out_count == 1
    assert report.final_count == 2


# ---------------------------------------------------------------------------
# 6. Integration with Elementary Jevons Index
# ---------------------------------------------------------------------------

def test_cleaning_integration_with_elementary_index():
    # Verify that clean quotes with sold-out flights feed properly into matched-sample Jevons
    d0 = date(2026, 9, 1)
    d1 = date(2026, 9, 2)

    # 6E is present both days, AI is sold out on day 2
    raw_quotes = [
        FareQuote(
            collected_at_utc=datetime(2026, 8, 25, tzinfo=timezone.utc),
            departure_date=d0,
            advance_window_days=7,
            origin_iata="DEL",
            destination_iata="BOM",
            carrier_iata="6E",
            fare_class="Economy",
            total_fare_inr=5000.0,
            source_id="test",
            collection_method="api",
            quality_flag="ok",
        ),
        FareQuote(
            collected_at_utc=datetime(2026, 8, 25, tzinfo=timezone.utc),
            departure_date=d0,
            advance_window_days=7,
            origin_iata="DEL",
            destination_iata="BOM",
            carrier_iata="AI",
            fare_class="Economy",
            total_fare_inr=6000.0,
            source_id="test",
            collection_method="api",
            quality_flag="ok",
        ),
        FareQuote(
            collected_at_utc=datetime(2026, 8, 26, tzinfo=timezone.utc),
            departure_date=d1,
            advance_window_days=7,
            origin_iata="DEL",
            destination_iata="BOM",
            carrier_iata="6E",
            fare_class="Economy",
            total_fare_inr=5500.0,
            source_id="test",
            collection_method="api",
            quality_flag="ok",
        ),
        FareQuote(
            collected_at_utc=datetime(2026, 8, 26, tzinfo=timezone.utc),
            departure_date=d1,
            advance_window_days=7,
            origin_iata="DEL",
            destination_iata="BOM",
            carrier_iata="AI",
            fare_class="Economy",
            total_fare_inr=None,
            source_id="test",
            collection_method="scrape",
            quality_flag="sold_out",
        ),
    ]

    pipeline = CleaningPipeline(impute_missing=False)
    cleaned, report = pipeline.clean_quotes(raw_quotes)

    # Construct daily price maps for Jevons
    daily_prices = [
        {q.carrier_iata: q.total_fare_inr for q in cleaned if q.departure_date == d0 and q.total_fare_inr is not None},
        {q.carrier_iata: q.total_fare_inr for q in cleaned if q.departure_date == d1 and q.total_fare_inr is not None},
    ]

    # AI is omitted on day 2 because total_fare_inr is None
    assert "AI" not in daily_prices[1]
    assert "6E" in daily_prices[1]

    # Matched-sample Jevons should only compare 6E (5500 / 5000 = 1.10)
    index = build_elementary_index(daily_prices, base_value=100.0)
    assert len(index) == 2
    assert index[0] == 100.0
    assert abs(index[1] - 110.0) < 1e-4


# ---------------------------------------------------------------------------
# 7. Kaggle EaseMyTrip Real-World Panel Cleanliness Test
# ---------------------------------------------------------------------------

def test_cleaning_pipeline_on_kaggle_sample():
    records = KaggleDatasetLoader.load_records(FIXTURE_PATH, window_strategy="exact")
    raw_quotes = [r.to_fare_quote() for r in records]

    pipeline = CleaningPipeline(
        deduplicate=True,
        detect_outliers=True,
        impute_missing=False,
    )
    cleaned, report = pipeline.clean_quotes(raw_quotes)

    # All quotes from valid fixture should pass validation
    assert report.total_input == len(raw_quotes)
    assert report.valid_count == len(raw_quotes)
    assert report.invalid_count == 0
    assert len(cleaned) == report.final_count
    # All cleaned quotes must be valid
    for q in cleaned:
        assert q.total_fare_inr is not None
        assert q.total_fare_inr > 0.0


if __name__ == "__main__":
    test_schema_valid_quote()
    test_schema_reject_zero_and_negative_fares()
    test_schema_sold_out_consistency()
    test_schema_invalid_iata_and_route()
    test_clean_quote_dict_auto_repair()
    test_deduplication_prefers_api_over_scrape()
    test_deduplication_prefers_latest_timestamp()
    test_outlier_detection_log_tukey()
    test_outlier_detection_zero_dispersion()
    test_outlier_detection_small_sample()
    test_imputation_class_mean_and_provenance()
    test_pipeline_end_to_end()
    test_cleaning_integration_with_elementary_index()
    test_cleaning_pipeline_on_kaggle_sample()
    print("All cleaning unit tests passed successfully!")


# ---------------------------------------------------------------------------
# Outlier basis regression tests
#
# Outlier screening used to run on the daily CROSS-SECTION of carriers, which
# flags a carrier for being priced differently from its competitors. That is a
# genuine market feature, not a data error, and excluding it biases the index
# toward the cheapest carrier. Screening now runs on each carrier's own
# period-to-period price relatives.
# ---------------------------------------------------------------------------

def _series_quote(day: int, carrier: str, price, window: int = 7) -> FareQuote:
    return FareQuote(
        collected_at_utc=datetime(2026, 1, 1, tzinfo=timezone.utc),
        departure_date=date(2026, 1, day),
        advance_window_days=window,
        origin_iata="DEL",
        destination_iata="BOM",
        carrier_iata=carrier,
        fare_class="Economy",
        total_fare_inr=price,
        source_id="test",
        collection_method="api",
        quality_flag="ok",
    )


def _stable_two_carrier_panel(days: int = 12):
    """A cheap LCC and a persistently pricier full-service carrier. No errors."""
    quotes = []
    for d in range(1, days + 1):
        quotes.append(_series_quote(d, "6E", 5000.0 + d * 10))
        quotes.append(_series_quote(d, "AI", 9000.0 + d * 10))
    return quotes


def test_relative_method_does_not_flag_legitimate_carrier_premium():
    """A carrier that is simply pricier than its rivals is not an outlier."""
    from apix.cleaning.outliers import detect_outliers

    _, flagged = detect_outliers(_stable_two_carrier_panel(), method="relative")
    assert flagged == 0, (
        f"Flagged {flagged} quotes on a panel containing only legitimate, "
        "stable carrier price dispersion."
    )


def test_relative_method_flags_a_genuine_price_spike():
    """A single carrier jumping 6x against its own history is an outlier."""
    from apix.cleaning.outliers import detect_outliers

    quotes = _stable_two_carrier_panel()
    quotes.append(_series_quote(13, "6E", 31000.0))   # ~6x its own level
    quotes.append(_series_quote(13, "AI", 9130.0))    # normal continuation

    result, flagged = detect_outliers(quotes, method="relative")
    assert flagged == 1, f"Expected exactly one outlier, got {flagged}."

    tagged = [q for q in result if q.quality_flag == "outlier"]
    assert tagged[0].carrier_iata == "6E"
    assert tagged[0].total_fare_inr == 31000.0


def test_outliers_are_tagged_never_deleted():
    """Screening must preserve every row for audit."""
    from apix.cleaning.outliers import detect_outliers

    quotes = _stable_two_carrier_panel()
    quotes.append(_series_quote(13, "6E", 31000.0))
    result, _ = detect_outliers(quotes, method="relative")
    assert len(result) == len(quotes)


def test_pipeline_defaults_to_relative_outlier_basis():
    from apix.cleaning.pipeline import CleaningPipeline

    assert CleaningPipeline().outlier_method == "relative"

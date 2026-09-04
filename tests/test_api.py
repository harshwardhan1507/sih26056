"""
Unit tests for APIx FastAPI service (Issue #12).

Tests:
  - Happy paths for all 7 endpoints against existing data artifacts
  - Query parameter filtering on /quotes and /index/elementary
  - Graceful fallback for /routes (placeholder flag) when weight file is absent
  - Graceful degradation (HTTP 503 with ErrorResponse) on missing data files
  - Empty pipeline reporting (HTTP 200 with zero counts) on /sources/status and /quality
  - Request validation error handling (HTTP 422 with ErrorResponse)
"""

import math
from datetime import date
from pathlib import Path
import sys
import tempfile

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient
from apix.api.main import app
from apix.api import data_access

client = TestClient(app)


def test_get_health():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"
    assert "timestamp_utc" in data


def test_get_routes_success():
    response = client.get("/routes")
    assert response.status_code == 200
    data = response.json()
    assert "source" in data
    assert data["source"] != "placeholder"
    assert len(data["routes"]) == 12

    # Verify weights sum to ~1.0
    total_weight = sum(r["weight"] for r in data["routes"])
    assert math.isclose(total_weight, 1.0, abs_tol=1e-4)


def test_get_routes_placeholder_fallback(monkeypatch):
    # Point data access to empty directory to trigger placeholder fallback
    with tempfile.TemporaryDirectory() as tmpdir:
        monkeypatch.setattr(data_access, "DEFAULT_DATA_DIR", Path(tmpdir))
        response = client.get("/routes")
        assert response.status_code == 200
        data = response.json()
        assert data["source"] == "placeholder"
        assert len(data["routes"]) == 12
        total_weight = sum(r["weight"] for r in data["routes"])
        assert math.isclose(total_weight, 1.0, abs_tol=1e-4)


def test_get_quotes_happy_path_and_filters():
    # 1. Unfiltered quotes
    response = client.get("/quotes")
    assert response.status_code == 200
    data = response.json()
    assert "count" in data
    assert "quotes" in data
    assert data["count"] > 0
    first_q = data["quotes"][0]
    assert "origin_iata" in first_q
    assert "destination_iata" in first_q
    assert "carrier_iata" in first_q
    assert "collection_method" in first_q
    assert "quality_flag" in first_q

    # 2. Filter by route (DEL-BOM)
    resp_route = client.get("/quotes?origin=DEL&destination=BOM")
    assert resp_route.status_code == 200
    data_route = resp_route.json()
    assert data_route["count"] > 0
    assert all(q["origin_iata"] == "DEL" and q["destination_iata"] == "BOM" for q in data_route["quotes"])

    # 3. Filter by advance window (7)
    resp_win = client.get("/quotes?origin=DEL&destination=BOM&advance_window_days=7")
    assert resp_win.status_code == 200
    data_win = resp_win.json()
    assert data_win["count"] > 0
    assert all(q["advance_window_days"] == 7 for q in data_win["quotes"])

    # 4. Filter by date range
    resp_date = client.get("/quotes?date_from=2026-01-01&date_to=2026-01-03")
    assert resp_date.status_code == 200
    data_date = resp_date.json()
    assert data_date["count"] > 0
    for q in data_date["quotes"]:
        dep = date.fromisoformat(q["departure_date"])
        assert date(2026, 1, 1) <= dep <= date(2026, 1, 3)


def test_get_aggregate_index():
    response = client.get("/index/aggregate")
    assert response.status_code == 200
    data = response.json()
    assert data["base_value"] == 100.0
    assert data["series_length"] > 0
    assert len(data["series"]) == data["series_length"]

    first_pt = data["series"][0]
    assert first_pt["day"] == 0
    assert first_pt["index_value"] == 100.0


def test_get_elementary_index():
    response = client.get("/index/elementary?origin=DEL&destination=BOM&advance_window_days=7")
    assert response.status_code == 200
    data = response.json()
    assert data["origin"] == "DEL"
    assert data["destination"] == "BOM"
    assert data["advance_window_days"] == 7
    assert data["base_value"] == 100.0
    assert data["series_length"] > 0

    first_pt = data["series"][0]
    assert first_pt["day"] == 0
    assert first_pt["index_value"] == 100.0
    assert first_pt["carrier_count"] > 0


def test_get_sources_status():
    response = client.get("/sources/status")
    assert response.status_code == 200
    data = response.json()
    assert data["total_quotes"] > 0
    assert "simulated" in data["by_method"]
    assert "fallback_simulated_percentage" in data
    assert 0.0 <= data["fallback_simulated_percentage"] <= 100.0
    assert "status_note" in data


def test_get_quality():
    response = client.get("/quality")
    assert response.status_code == 200
    data = response.json()
    assert data["total_quotes"] > 0
    assert "by_quality_flag" in data
    assert "ok_count" in data
    assert "sold_out_count" in data
    assert "outlier_count" in data
    assert "imputed_count" in data
    assert data["ok_count"] > 0


def test_missing_data_errors(monkeypatch):
    with tempfile.TemporaryDirectory() as tmpdir:
        # Point to an empty directory where no data files exist
        monkeypatch.setattr(data_access, "DEFAULT_DATA_DIR", Path(tmpdir))

        # 1. /quotes should return 503 with ErrorResponse
        resp_quotes = client.get("/quotes")
        assert resp_quotes.status_code == 503
        err_quotes = resp_quotes.json()
        assert err_quotes["error"] == "data_unavailable"
        assert "fare_quote.csv" in err_quotes["detail"]

        # 2. /index/aggregate should return 503 with ErrorResponse
        resp_agg = client.get("/index/aggregate")
        assert resp_agg.status_code == 503
        err_agg = resp_agg.json()
        assert err_agg["error"] == "data_unavailable"
        assert "index_series.csv" in err_agg["detail"]

        # 3. /index/elementary should return 503 with ErrorResponse
        resp_elem = client.get("/index/elementary?origin=DEL&destination=BOM&advance_window_days=7")
        assert resp_elem.status_code == 503
        err_elem = resp_elem.json()
        assert err_elem["error"] == "data_unavailable"

        # 4. /sources/status must return 200 with zero counts (empty pipeline is valid)
        resp_status = client.get("/sources/status")
        assert resp_status.status_code == 200
        data_status = resp_status.json()
        assert data_status["total_quotes"] == 0
        assert data_status["fallback_simulated_percentage"] == 0.0

        # 5. /quality must return 200 with zero counts
        resp_qual = client.get("/quality")
        assert resp_qual.status_code == 200
        data_qual = resp_qual.json()
        assert data_qual["total_quotes"] == 0
        assert data_qual["ok_count"] == 0


def test_validation_errors():
    # Missing required query param origin on /index/elementary
    response = client.get("/index/elementary?destination=BOM&advance_window_days=7")
    assert response.status_code == 422
    data = response.json()
    assert data["error"] == "validation_error"
    assert "origin" in data["detail"]

    # Invalid integer for advance_window_days
    resp_invalid = client.get("/quotes?advance_window_days=not_an_int")
    assert resp_invalid.status_code == 422
    data_invalid = resp_invalid.json()
    assert data_invalid["error"] == "validation_error"


if __name__ == "__main__":
    test_get_health()
    test_get_routes_success()
    test_get_quotes_happy_path_and_filters()
    test_get_aggregate_index()
    test_get_elementary_index()
    test_get_sources_status()
    test_get_quality()
    test_validation_errors()
    print("All API unit tests passed successfully!")

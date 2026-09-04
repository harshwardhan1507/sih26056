"""
Unit tests for DGCA passenger route weight derivation (scripts/derive_weights.py).
"""

import csv
import math
import sys
from io import StringIO
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from scripts.derive_weights import (
    BASKET_ROUTES,
    build_weight_payload,
    canonicalize_route,
    derive_weights_from_reader,
    is_in_period,
    map_city_to_iata,
)


def test_map_city_to_iata_standard_metros():
    assert map_city_to_iata("DELHI") == "DEL"
    assert map_city_to_iata("Delhi") == "DEL"
    assert map_city_to_iata("New Delhi") == "DEL"
    assert map_city_to_iata("BENGALURU") == "BLR"
    assert map_city_to_iata("Bangalore") == "BLR"
    assert map_city_to_iata("KOLKATA") == "CCU"
    assert map_city_to_iata("Calcutta") == "CCU"
    assert map_city_to_iata("CHENNAI") == "MAA"
    assert map_city_to_iata("Madras") == "MAA"
    assert map_city_to_iata("HYDERABAD") == "HYD"


def test_map_city_to_iata_multi_airports():
    # Mumbai dual-airport
    assert map_city_to_iata("MUMBAI") == "BOM"
    assert map_city_to_iata("MUMBAI (MUMBAI)") == "BOM"
    assert map_city_to_iata("MUMBAI (NAVI MUMBAI)") == "BOM"

    # Goa dual-airport across historical phases
    assert map_city_to_iata("GOA") == "GOI"
    assert map_city_to_iata("DABOLIM") == "GOI"
    assert map_city_to_iata("MOPA, GOA") == "GOI"
    assert map_city_to_iata("MOPA") == "GOI"
    assert map_city_to_iata("GOA (DABOLIM, SOUTH GOA)") == "GOI"
    assert map_city_to_iata("GOA (MOPA, NORTH GOA)") == "GOI"


def test_map_city_to_iata_unmapped():
    assert map_city_to_iata("PUNE") is None
    assert map_city_to_iata("JAIPUR") is None
    assert map_city_to_iata("UNKNOWN") is None


def test_canonicalize_route_bidirectional():
    # Forward
    assert canonicalize_route("DELHI", "MUMBAI") == "DEL-BOM"
    # Reverse
    assert canonicalize_route("MUMBAI", "DELHI") == "DEL-BOM"
    assert canonicalize_route("MUMBAI (MUMBAI)", "DELHI") == "DEL-BOM"

    # Goa routes with dual-airport strings
    assert canonicalize_route("DELHI", "GOA (MOPA, NORTH GOA)") == "DEL-GOI"
    assert canonicalize_route("GOA (DABOLIM, SOUTH GOA)", "DELHI") == "DEL-GOI"
    assert canonicalize_route("MOPA, GOA", "MUMBAI") == "BOM-GOI"
    assert canonicalize_route("DABOLIM", "MUMBAI") == "BOM-GOI"

    # Non-basket routes
    assert canonicalize_route("DELHI", "PUNE") is None
    assert canonicalize_route("CHENNAI", "KOLKATA") is None


def test_is_in_period():
    assert is_in_period(2025, 6, "2025-06", "2026-05") is True
    assert is_in_period(2025, 12, "2025-06", "2026-05") is True
    assert is_in_period(2026, 1, "2025-06", "2026-05") is True
    assert is_in_period(2026, 5, "2025-06", "2026-05") is True

    # Out of bounds
    assert is_in_period(2025, 5, "2025-06", "2026-05") is False
    assert is_in_period(2026, 6, "2025-06", "2026-05") is False
    assert is_in_period(2024, 12, "2025-06", "2026-05") is False


def test_derive_weights_from_reader():
    sample_csv = """Year,Month,City1,City2,PaxToCity2,PaxFromCity2,FreightToCity2,FreightFromCity2,MailToCity2,MailFromCity2
2025,6,DELHI,MUMBAI,10000,10000,0,0,0,0
2025,7,MUMBAI,DELHI,5000,5000,0,0,0,0
2025,8,DELHI,BENGALURU,8000,7000,0,0,0,0
2025,9,DELHI,KOLKATA,5000,4000,0,0,0,0
2025,10,DELHI,CHENNAI,4000,4000,0,0,0,0
2025,11,DELHI,HYDERABAD,5000,5000,0,0,0,0
2025,12,MUMBAI,BENGALURU,6000,5000,0,0,0,0
2026,1,MUMBAI,CHENNAI,3500,3500,0,0,0,0
2026,2,MUMBAI,KOLKATA,3000,3000,0,0,0,0
2026,3,BENGALURU,HYDERABAD,3000,3000,0,0,0,0
2026,4,BENGALURU,CHENNAI,2000,2000,0,0,0,0
2026,5,DELHI,"GOA (DABOLIM, SOUTH GOA)",1500,1500,0,0,0,0
2026,5,DELHI,"GOA (MOPA, NORTH GOA)",1000,1000,0,0,0,0
2026,5,MUMBAI,"GOA (MOPA, NORTH GOA)",1000,1000,0,0,0,0
2025,5,DELHI,MUMBAI,50000,50000,0,0,0,0
2026,6,DELHI,MUMBAI,50000,50000,0,0,0,0
2025,6,DELHI,PATNA,20000,20000,0,0,0,0
"""
    reader = csv.DictReader(StringIO(sample_csv))
    weights, route_pax, total_basket_pax, all_domestic_pax = derive_weights_from_reader(
        reader,
        start_period="2025-06",
        end_period="2026-05",
    )

    # Verify all 12 routes are present
    assert len(weights) == 12
    for r in BASKET_ROUTES:
        assert r in weights
        assert weights[r] > 0.0

    # Verify weights sum to 1.0 within tolerance
    assert math.isclose(sum(weights.values()), 1.0, abs_tol=1e-5)

    # Verify Goa multi-airport aggregation (DEL-GOI has 1500+1500 + 1000+1000 = 5000)
    assert route_pax["DEL-GOI"] == 5000

    # Verify non-basket route PATNA is in all_domestic_pax but not total_basket_pax
    assert all_domestic_pax > total_basket_pax


def test_build_weight_payload():
    weights = {"DEL-BOM": 0.20, "DEL-BLR": 0.15, "DEL-CCU": 0.65}
    route_pax = {"DEL-BOM": 20000, "DEL-BLR": 15000, "DEL-CCU": 65000}
    payload = build_weight_payload(
        weights=weights,
        route_pax=route_pax,
        total_basket_pax=100000,
        coverage_month="2026-05",
        t12m_start="2025-06",
        t12m_end="2026-05",
    )

    assert "source" in payload
    assert payload["coverage_month"] == "2026-05"
    assert "2025-06 to 2026-05" in payload["methodology"]
    assert payload["total_basket_pax"] == 100000
    assert "DEL-CCU" == next(iter(payload["weights"].keys()))


if __name__ == "__main__":
    test_map_city_to_iata_standard_metros()
    test_map_city_to_iata_multi_airports()
    test_map_city_to_iata_unmapped()
    test_canonicalize_route_bidirectional()
    test_is_in_period()
    test_derive_weights_from_reader()
    test_build_weight_payload()
    print("All derive_weights unit tests passed successfully!")

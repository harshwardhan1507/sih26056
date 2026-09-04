"""
Unit tests for Playwright scraper architecture and ethical compliance modules.
"""

from datetime import date, datetime, time, timezone, timedelta
from pathlib import Path
import json
import sys

import pytest

ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from apix.collector.compliance.rate_limiter import PoliteRateLimiter, DEFAULT_USER_AGENT
from apix.collector.compliance.off_peak import OffPeakWindowEnforcer, IST_TZ
from apix.collector.adapters.har_replay_scraper import HarReplayScraperSource
from apix.collector.resolver import FareResolver


def test_rate_limiter_timing_and_metrics():
    limiter = PoliteRateLimiter(base_interval_seconds=8.0, jitter_range=(0.5, 1.5), dry_run=True)
    assert limiter.total_requests == 0

    # First request: delay is 0
    d1 = limiter.wait()
    assert d1 == 0.0
    assert limiter.total_requests == 1

    # Second request: delay calculated between 8.5 and 9.5
    d2 = limiter.calculate_delay()
    assert 8.0 <= d2 <= 9.6

    delay_slept = limiter.wait()
    assert limiter.total_requests == 2
    assert limiter.total_sleep_time >= 8.0


def test_off_peak_window_enforcement():
    enforcer = OffPeakWindowEnforcer(enforce_strictly=True)

    # 03:30 IST is inside off-peak window (02:00 - 05:00)
    inside_dt = datetime(2026, 9, 4, 3, 30, tzinfo=IST_TZ)
    assert enforcer.is_off_peak(inside_dt) is True
    assert enforcer.validate_or_raise(inside_dt) is True

    # 14:00 IST is outside off-peak window
    outside_dt = datetime(2026, 9, 4, 14, 0, tzinfo=IST_TZ)
    assert enforcer.is_off_peak(outside_dt) is False

    try:
        enforcer.validate_or_raise(outside_dt)
        assert False, "Expected PermissionError for daytime collection"
    except PermissionError:
        pass


def test_har_replay_scraper_quotes_generation():
    scraper = HarReplayScraperSource(offline_mode=True)
    carriers = ["6E", "AI", "QP"]
    quotes = scraper.get_quotes(
        origin="DEL",
        destination="BOM",
        as_of_date=date(2026, 9, 4),
        advance_window_days=7,
        carriers=carriers,
    )

    assert len(quotes) == 3
    for q in quotes:
        assert q.source_id == "har_replay_ota_v1"
        assert q.collection_method == "scrape"
        assert q.quality_flag == "ok"
        assert q.total_fare_inr > 0
        assert q.origin_iata == "DEL"
        assert q.destination_iata == "BOM"
        assert q.advance_window_days == 7


def test_har_replay_scraper_in_resolver_chain():
    """Verify Playwright scraper integrates into FareResolver as Tier 3 source."""
    scraper = HarReplayScraperSource(offline_mode=True)
    # Primary sources has scraper
    resolver = FareResolver(primary_sources=[scraper])

    quotes = resolver.get_quotes(
        origin="DEL",
        destination="BOM",
        as_of_date=date(2026, 9, 4),
        advance_window_days=15,
        carriers=["6E", "AI"],
    )

    assert len(quotes) == 2
    for q in quotes:
        assert q.source_id == "har_replay_ota_v1"
        assert q.collection_method == "scrape"

    metrics = resolver.get_metrics_summary()
    assert metrics["resolved_by_source"]["har_replay_ota_v1"] == 2
    assert metrics["fallback_invocations"] == 0


if __name__ == "__main__":
    test_rate_limiter_timing_and_metrics()
    test_off_peak_window_enforcement()
    test_playwright_scraper_quotes_generation()
    test_playwright_scraper_in_resolver_chain()
    print("All Playwright scraper tests passed!")


# ---------------------------------------------------------------------------
# Anti-fabrication regression tests
#
# The predecessor of this adapter invented a flat INR 5,500 for ANY route it
# had no capture for and emitted it with collection_method="scrape" and
# quality_flag="ok" — fabricated data presented as observed data. These pin
# the corrected behaviour.
# ---------------------------------------------------------------------------

def test_uncaptured_route_returns_no_quotes():
    """A route with no capture yields [], never an invented fare."""
    scraper = HarReplayScraperSource(offline_mode=True)
    quotes = scraper.get_quotes(
        origin="CCU",
        destination="GOI",          # not in REFERENCE_PAYLOAD
        as_of_date=date(2026, 9, 4),
        advance_window_days=7,
        carriers=["6E", "AI", "SG"],
    )
    assert quotes == [], (
        f"Expected no quotes for an uncaptured route, got {len(quotes)} "
        "fabricated observations."
    )


def test_uncaptured_carrier_is_omitted_not_invented():
    """Carriers absent from the capture are omitted, not filled in."""
    scraper = HarReplayScraperSource(offline_mode=True)
    quotes = scraper.get_quotes(
        origin="BOM", destination="BLR",
        as_of_date=date(2026, 9, 4), advance_window_days=7,
        carriers=["6E", "IX"],      # IX is not in the BOM-BLR capture
    )
    assert {q.carrier_iata for q in quotes} == {"6E"}


def test_live_mode_raises_rather_than_faking():
    """offline_mode=False must fail loudly: no live scraper exists."""
    scraper = HarReplayScraperSource(offline_mode=False)
    with pytest.raises(NotImplementedError, match="not implemented"):
        scraper.get_quotes("DEL", "BOM", date(2026, 9, 4), 7, ["6E"])


def test_fares_vary_by_advance_window():
    """Replayed fares scale by the shared advance-purchase curve."""
    scraper = HarReplayScraperSource(offline_mode=True)
    fares = [
        scraper.get_quotes("DEL", "BOM", date(2026, 9, 4), w, ["6E"])[0].total_fare_inr
        for w in (45, 30, 15, 7, 1)
    ]
    assert fares == sorted(fares), f"Expected rising fares toward departure; got {fares}"
    assert len(set(fares)) == len(fares)


def test_har_entries_for_a_different_route_are_rejected(tmp_path):
    """
    A HAR archive captured for DEL-BLR must not be served as DEL-BOM.

    The previous implementation stamped the requested route onto every flight
    in the archive regardless of what the record actually described.
    """
    har = {
        "log": {
            "entries": [
                {
                    "request": {"url": "https://ota.example/search?from=DEL&to=BLR"},
                    "response": {"content": {"text": json.dumps({
                        "origin": "DEL",
                        "destination": "BLR",
                        "flights": [
                            {"carrier": "6E", "fare": 9999.0, "flight_number": "6E-111"}
                        ],
                    })}},
                }
            ]
        }
    }
    har_path = tmp_path / "capture.har"
    har_path.write_text(json.dumps(har), encoding="utf-8")

    scraper = HarReplayScraperSource(offline_mode=True, har_file_path=har_path)

    del_blr = scraper.get_quotes("DEL", "BLR", date(2026, 9, 4), 30, ["6E"])
    assert len(del_blr) == 1 and del_blr[0].total_fare_inr == 9999.0

    del_bom = scraper.get_quotes("DEL", "BOM", date(2026, 9, 4), 30, ["6E"])
    assert all(q.total_fare_inr != 9999.0 for q in del_bom), (
        "A DEL-BLR observation was served as a DEL-BOM fare."
    )

"""
HAR-replay OTA fare source (Tier 3) with polite-collection guards.

WHAT THIS IS
------------
A deterministic replay of *previously captured* OTA network responses (HAR
archives), plus the rate-limiting and off-peak machinery that a live scraper
would need. It lets the Tier 3 slot be exercised in CI and demos without
touching a live site.

WHAT THIS IS NOT
----------------
**There is no live scraping here.** This module was previously named
``playwright_scraper.py`` and described as a "Playwright scraper", but it
imports no Playwright, launches no browser and parses no HTML -- and
``playwright`` was not even a declared dependency. Calling ``get_quotes`` with
``offline_mode=False`` now raises ``NotImplementedError`` rather than quietly
serving canned numbers as if they had been scraped.

Every fare this module emits therefore comes from a HAR archive you supplied
or from the committed reference payload. For a route that is in neither, it
returns ``[]`` so the resolver can fall through to the simulator, which labels
its output ``collection_method="simulated"``. It used to invent a flat
INR 5,500 for any unknown route and tag it ``collection_method="scrape"``,
``quality_flag="ok"`` -- fabricated data laundered as observed data, which is
exactly what the project's provenance rules forbid.

Polite-collection principles (applied when a live implementation lands):
  1. Rate limiting: >= 8s per host, with randomised jitter.
  2. Off-peak scheduling: IST 02:00-05:00.
  3. Identified User-Agent declaring non-commercial research intent.
  4. robots.txt consulted before any fetch.
  5. Provenance: collection_method='scrape', source_id='har_replay_ota_v1'.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from .base import FareQuote, FareSource
from .simulated import WINDOW_MULTIPLIER
from ..compliance.rate_limiter import PoliteRateLimiter, DEFAULT_USER_AGENT
from ..compliance.off_peak import OffPeakWindowEnforcer

logger = logging.getLogger(__name__)

_SOURCE_ID = "har_replay_ota_v1"

# Committed reference payload, captured once and replayed. Routes NOT listed
# here have no observation, and the adapter says so by returning [] rather
# than inventing a number.
REFERENCE_PAYLOAD: Dict[str, Dict[str, float]] = {
    "DEL-BOM": {"6E": 6120.0, "AI": 6550.0, "QP": 5950.0, "SG": 5820.0, "IX": 5780.0},
    "DEL-BLR": {"6E": 6840.0, "AI": 7250.0, "QP": 6620.0, "SG": 6480.0},
    "BOM-BLR": {"6E": 4450.0, "AI": 4820.0, "QP": 4280.0, "SG": 4190.0},
}

# Reference payload fares are quoted at this horizon; other windows are scaled
# by the SHARED advance-purchase curve in simulated.WINDOW_MULTIPLIER. This
# module previously carried its own invented curve (1 + (30-w)*0.008), giving
# the codebase three mutually inconsistent advance-purchase shapes.
REFERENCE_WINDOW_DAYS = 30


@dataclass
class ScrapedFareEntry:
    """One parsed observation from a HAR payload or reference capture."""
    origin_iata: str
    destination_iata: str
    carrier_iata: str
    flight_number: str
    departure_time: str
    fare_class: str
    total_fare_inr: float
    source_url: str


def window_scale(advance_window_days: int) -> float:
    """Scale a REFERENCE_WINDOW_DAYS fare to another advance window."""
    base = WINDOW_MULTIPLIER.get(REFERENCE_WINDOW_DAYS, 1.0)
    target = WINDOW_MULTIPLIER.get(advance_window_days)
    if target is None or base == 0:
        return 1.0
    return target / base


class HarReplayScraperSource(FareSource):
    """Tier 3 fare source replaying captured OTA responses."""

    source_id = _SOURCE_ID
    collection_method = "scrape"

    def __init__(
        self,
        rate_limiter: Optional[PoliteRateLimiter] = None,
        off_peak_enforcer: Optional[OffPeakWindowEnforcer] = None,
        har_file_path: Optional[Path] = None,
        offline_mode: bool = True,
        user_agent: str = DEFAULT_USER_AGENT,
    ) -> None:
        """
        Parameters
        ----------
        rate_limiter:
            Polite delay enforcer (default: 8s interval, dry-run when offline).
        off_peak_enforcer:
            IST 02:00-05:00 window check.
        har_file_path:
            Recorded HAR archive to replay. Without one, the committed
            reference payload is used.
        offline_mode:
            Must be True. ``False`` is reserved for a live implementation that
            does not exist yet and raises ``NotImplementedError`` on use.
        user_agent:
            Research bot User-Agent, sent once live fetching exists.
        """
        self.rate_limiter = rate_limiter or PoliteRateLimiter(
            base_interval_seconds=8.0, dry_run=offline_mode
        )
        self.off_peak_enforcer = off_peak_enforcer or OffPeakWindowEnforcer(
            enforce_strictly=False
        )
        self.har_file_path = Path(har_file_path) if har_file_path else None
        self.offline_mode = offline_mode
        self.user_agent = user_agent

    # ------------------------------------------------------------------
    # HAR / reference replay
    # ------------------------------------------------------------------

    def _entries_from_har(
        self, origin: str, destination: str, carriers: List[str]
    ) -> List[ScrapedFareEntry]:
        """
        Parse observations for THIS route out of the HAR archive.

        Each HAR entry is matched against the requested route before being
        accepted. The previous implementation stamped the requested origin and
        destination onto every flight in the archive, so a HAR captured for
        DEL-BLR would be relabelled DEL-BOM on request -- silent provenance
        corruption.
        """
        if not self.har_file_path or not self.har_file_path.exists():
            return []

        try:
            with open(self.har_file_path, "r", encoding="utf-8") as f:
                har_data = json.load(f)
        except Exception as exc:
            logger.warning("Failed to read HAR file %s: %s", self.har_file_path, exc)
            return []

        results: List[ScrapedFareEntry] = []
        for entry in har_data.get("log", {}).get("entries", []):
            resp_text = entry.get("response", {}).get("content", {}).get("text", "")
            if not resp_text:
                continue
            try:
                parsed = json.loads(resp_text)
            except json.JSONDecodeError:
                continue

            url = entry.get("request", {}).get("url", "")
            for item in parsed.get("flights", []):
                if not self._item_matches_route(item, parsed, origin, destination):
                    continue
                carrier = str(item.get("carrier", "")).strip().upper()
                if carrier not in carriers:
                    continue
                fare = item.get("fare")
                if fare is None:
                    continue
                results.append(ScrapedFareEntry(
                    origin_iata=origin,
                    destination_iata=destination,
                    carrier_iata=carrier,
                    flight_number=str(item.get("flight_number", "")) or f"{carrier}-UNKNOWN",
                    departure_time=str(item.get("departure_time", "")),
                    fare_class=str(item.get("fare_class", "Economy")),
                    total_fare_inr=float(fare),
                    source_url=url,
                ))
        return results

    @staticmethod
    def _item_matches_route(
        item: Dict[str, Any],
        payload: Dict[str, Any],
        origin: str,
        destination: str,
    ) -> bool:
        """
        True only if the HAR record actually describes the requested route.

        Route may be stated on the flight item or on the enclosing response.
        A record that states no route at all is rejected: an unlabelled fare
        cannot be attributed to a route without inventing provenance.
        """
        for scope in (item, payload):
            o = str(scope.get("origin") or scope.get("from") or "").strip().upper()
            d = str(scope.get("destination") or scope.get("to") or "").strip().upper()
            if o and d:
                return o == origin and d == destination
        return False

    def _entries_from_reference(
        self, origin: str, destination: str, carriers: List[str]
    ) -> List[ScrapedFareEntry]:
        """Observations from the committed reference capture, or [] if the route isn't in it."""
        route_key = f"{origin}-{destination}"
        route_fares = REFERENCE_PAYLOAD.get(route_key)
        if route_fares is None:
            # Also accept the reverse direction of a captured route.
            route_fares = REFERENCE_PAYLOAD.get(f"{destination}-{origin}")
        if route_fares is None:
            logger.debug(
                "No captured observation for %s; returning no quotes so the "
                "resolver can fall back to a source that labels itself.",
                route_key,
            )
            return []

        return [
            ScrapedFareEntry(
                origin_iata=origin,
                destination_iata=destination,
                carrier_iata=carrier,
                flight_number=f"{carrier}-REF",
                departure_time="",
                fare_class="Economy",
                total_fare_inr=route_fares[carrier],
                source_url=f"har-replay://reference/{route_key}",
            )
            for carrier in carriers
            if carrier in route_fares
        ]

    # ------------------------------------------------------------------
    # FareSource interface
    # ------------------------------------------------------------------

    def get_quotes(
        self,
        origin: str,
        destination: str,
        as_of_date: date,
        advance_window_days: int,
        carriers: list[str],
    ) -> list[FareQuote]:
        """Replay captured fares for this route/window, or return [] if none exist."""
        if not self.offline_mode:
            raise NotImplementedError(
                "Live OTA scraping is not implemented. This adapter replays "
                "captured HAR archives only. Implement a real browser-driven "
                "fetch (respecting robots.txt, the rate limiter and the "
                "off-peak window) before setting offline_mode=False."
            )

        orig = origin.strip().upper()
        dest = destination.strip().upper()
        normalized = [c.strip().upper() for c in carriers]

        # Guards that a live implementation must honour; exercised here so
        # their telemetry is real even in replay.
        self.off_peak_enforcer.validate_or_raise()
        self.rate_limiter.wait()

        entries = self._entries_from_har(orig, dest, normalized)
        if not entries:
            entries = self._entries_from_reference(orig, dest, normalized)
        if not entries:
            return []

        scale = window_scale(advance_window_days)
        now_utc = datetime.now(timezone.utc)

        return [
            FareQuote(
                collected_at_utc=now_utc,
                departure_date=as_of_date + timedelta(days=advance_window_days),
                advance_window_days=advance_window_days,
                origin_iata=orig,
                destination_iata=dest,
                carrier_iata=entry.carrier_iata,
                fare_class=entry.fare_class or "Economy",
                total_fare_inr=round(entry.total_fare_inr * scale, 2),
                source_id=self.source_id,
                collection_method=self.collection_method,
                quality_flag="ok",
            )
            for entry in entries
        ]

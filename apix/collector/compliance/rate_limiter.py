"""
Ethical Scraper Compliance — Polite Rate Limiter for APIx Tier 3 Collection.

Enforces:
  - A minimum request interval PER HOST (default 8.0s, i.e. 1 req / 8s)
  - Randomised additive jitter to avoid synchronised bursts
  - Identified User-Agent declaring the SIH-26056 research prototype

The limiter is genuinely per-host: it keeps one clock per hostname, so a
delay owed to one site does not throttle an unrelated one. It documented
itself as "host-aware" while keeping a single global clock, which both
over-throttled multi-host runs and under-reported per-host pressure.
"""

from __future__ import annotations

import random
import threading
import time
from typing import Dict, Optional
from urllib.parse import urlparse

DEFAULT_USER_AGENT = (
    "APIx-Research-Bot/1.0 "
    "(MoSPI SIH-26056 Non-Commercial Airfare Index Research; "
    "+https://github.com/harshwardhan1507/sih26056)"
)

# Host key used when a caller does not name one.
DEFAULT_HOST = "_default"


def host_of(url_or_host: str) -> str:
    """Normalise a URL or bare hostname to a lowercase host key."""
    if not url_or_host:
        return DEFAULT_HOST
    parsed = urlparse(url_or_host if "//" in url_or_host else f"//{url_or_host}")
    return (parsed.hostname or url_or_host).strip().lower()


class PoliteRateLimiter:
    """Per-host polite rate limiter with randomised jitter and telemetry."""

    def __init__(
        self,
        base_interval_seconds: float = 8.0,
        jitter_range: tuple[float, float] = (0.5, 2.0),
        dry_run: bool = False,
    ) -> None:
        """
        Parameters
        ----------
        base_interval_seconds:
            Minimum seconds between consecutive requests to the SAME host.
        jitter_range:
            (min, max) seconds added on top of ``base_interval_seconds``.
            Additive only, so the effective interval is never shorter than
            the base -- jitter spreads load, it does not buy speed.
        dry_run:
            Compute timings and telemetry without actually sleeping.
        """
        if base_interval_seconds < 0:
            raise ValueError("base_interval_seconds must be non-negative.")
        lo, hi = jitter_range
        if lo < 0 or hi < lo:
            raise ValueError(f"Invalid jitter_range {jitter_range}: expected 0 <= min <= max.")

        self.base_interval = base_interval_seconds
        self.jitter_range = jitter_range
        self.dry_run = dry_run

        self._last_request_time: Dict[str, float] = {}
        self._lock = threading.Lock()
        self.total_requests = 0
        self.total_sleep_time = 0.0
        self.requests_per_host: Dict[str, int] = {}

    def calculate_delay(self, host: Optional[str] = None) -> float:
        """Seconds this caller must wait before hitting ``host`` again."""
        key = host_of(host) if host else DEFAULT_HOST
        last = self._last_request_time.get(key)
        if last is None:
            return 0.0

        elapsed = time.time() - last
        jitter = random.uniform(self.jitter_range[0], self.jitter_range[1])
        return max(0.0, (self.base_interval + jitter) - elapsed)

    def wait(self, host: Optional[str] = None) -> float:
        """
        Enforce the per-host rate limit. Returns the seconds slept.

        ``host`` may be a full URL or a bare hostname; omitting it uses a
        single shared clock, which is the right behaviour for a single-site
        collector.
        """
        key = host_of(host) if host else DEFAULT_HOST

        with self._lock:
            delay = self.calculate_delay(key)

        if delay > 0 and not self.dry_run:
            time.sleep(delay)

        with self._lock:
            self.total_requests += 1
            self.total_sleep_time += delay
            self.requests_per_host[key] = self.requests_per_host.get(key, 0) + 1
            self._last_request_time[key] = time.time()

        return delay

    def reset(self) -> None:
        """Clear all per-host clocks and telemetry."""
        with self._lock:
            self._last_request_time.clear()
            self.requests_per_host.clear()
            self.total_requests = 0
            self.total_sleep_time = 0.0

    def metrics(self) -> dict:
        """Telemetry snapshot for the collection audit log."""
        return {
            "total_requests": self.total_requests,
            "total_sleep_seconds": round(self.total_sleep_time, 2),
            "base_interval_seconds": self.base_interval,
            "requests_per_host": dict(self.requests_per_host),
            "dry_run": self.dry_run,
        }

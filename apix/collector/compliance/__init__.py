"""Scraper compliance: rate limiting, robots.txt, off-peak windows, circuit breakers."""

from .rate_limiter import PoliteRateLimiter, DEFAULT_USER_AGENT, host_of
from .off_peak import OffPeakWindowEnforcer, IST_TZ, OFF_PEAK_START, OFF_PEAK_END
from .robots import RobotsPolicy, RobotsDisallowed
from .circuit_breaker import CircuitBreaker, CircuitOpenError, CLOSED, OPEN, HALF_OPEN

__all__ = [
    "PoliteRateLimiter",
    "DEFAULT_USER_AGENT",
    "host_of",
    "OffPeakWindowEnforcer",
    "IST_TZ",
    "OFF_PEAK_START",
    "OFF_PEAK_END",
    "RobotsPolicy",
    "RobotsDisallowed",
    "CircuitBreaker",
    "CircuitOpenError",
    "CLOSED",
    "OPEN",
    "HALF_OPEN",
]

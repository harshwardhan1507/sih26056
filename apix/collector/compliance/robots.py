"""
robots.txt compliance gate for APIx Tier 3 collection.

The architecture documentation has always listed robots.txt checking as part
of the compliance layer; this module supplies it. Any live fetch must pass
through ``RobotsPolicy.is_allowed`` before a request is made.

Behaviour on failure is deliberately conservative: if robots.txt cannot be
retrieved or parsed, the path is treated as DISALLOWED. A collector for a
national statistical office should not scrape a site whose wishes it could
not read.
"""

from __future__ import annotations

import logging
import threading
import urllib.error
import urllib.robotparser
from typing import Dict, Optional
from urllib.parse import urlparse, urlunparse

from .rate_limiter import DEFAULT_USER_AGENT

logger = logging.getLogger(__name__)

DEFAULT_TIMEOUT_SECONDS = 10.0


class RobotsDisallowed(PermissionError):
    """Raised when a URL is disallowed by the target site's robots.txt."""


class RobotsPolicy:
    """
    Caches and evaluates robots.txt for each host encountered.

    One parser per host is fetched at most once per process. Results are
    cached because re-fetching robots.txt on every request would itself be
    impolite.
    """

    def __init__(
        self,
        user_agent: str = DEFAULT_USER_AGENT,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        allow_on_fetch_error: bool = False,
    ) -> None:
        """
        allow_on_fetch_error:
            Leave False (the default). Setting it True means an unreachable
            robots.txt is treated as permission to crawl, which is the
            opposite of the conservative default a public-sector collector
            should adopt.
        """
        self.user_agent = user_agent
        self.timeout_seconds = timeout_seconds
        self.allow_on_fetch_error = allow_on_fetch_error
        self._parsers: Dict[str, Optional[urllib.robotparser.RobotFileParser]] = {}
        self._lock = threading.Lock()

    def _robots_url(self, url: str) -> Optional[str]:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            return None
        return urlunparse((parsed.scheme, parsed.netloc, "/robots.txt", "", "", ""))

    def _parser_for(self, url: str) -> Optional[urllib.robotparser.RobotFileParser]:
        parsed = urlparse(url)
        host_key = f"{parsed.scheme}://{parsed.netloc}".lower()

        with self._lock:
            if host_key in self._parsers:
                return self._parsers[host_key]

        robots_url = self._robots_url(url)
        parser: Optional[urllib.robotparser.RobotFileParser] = None
        if robots_url:
            candidate = urllib.robotparser.RobotFileParser()
            candidate.set_url(robots_url)
            try:
                candidate.read()
                parser = candidate
            except (urllib.error.URLError, OSError, ValueError) as exc:
                logger.warning(
                    "Could not read %s (%s); treating the host as disallowed.",
                    robots_url, exc,
                )
                parser = None

        with self._lock:
            self._parsers[host_key] = parser
        return parser

    def is_allowed(self, url: str) -> bool:
        """True if this URL may be fetched under the target site's robots.txt."""
        parser = self._parser_for(url)
        if parser is None:
            return self.allow_on_fetch_error
        try:
            return parser.can_fetch(self.user_agent, url)
        except Exception as exc:
            logger.warning("robots.txt evaluation failed for %s: %s", url, exc)
            return self.allow_on_fetch_error

    def crawl_delay(self, url: str) -> Optional[float]:
        """
        Crawl-delay the site requests, if any.

        A site asking for more than the collector's own floor must win: call
        this and pass the larger value to the rate limiter.
        """
        parser = self._parser_for(url)
        if parser is None:
            return None
        try:
            delay = parser.crawl_delay(self.user_agent)
            return float(delay) if delay is not None else None
        except Exception:
            return None

    def validate_or_raise(self, url: str) -> None:
        """Raise ``RobotsDisallowed`` unless this URL may be fetched."""
        if not self.is_allowed(url):
            raise RobotsDisallowed(
                f"robots.txt for {urlparse(url).netloc} disallows {url} for "
                f"user-agent {self.user_agent!r}. Collection must not proceed."
            )

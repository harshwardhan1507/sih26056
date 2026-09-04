"""
Circuit breaker for APIx collection sources.

Listed in the architecture docs alongside rate limiting and robots.txt; this
module supplies it. It stops the collector from hammering a source that is
already failing -- both to avoid load on someone else's infrastructure and to
keep a broken tier from stalling the daily run.

States
------
  CLOSED    normal; calls pass through
  OPEN      too many recent failures; calls are refused immediately
  HALF_OPEN cooldown elapsed; one trial call is admitted to test recovery
"""

from __future__ import annotations

import logging
import threading
import time
from typing import Callable, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")

CLOSED = "closed"
OPEN = "open"
HALF_OPEN = "half_open"


class CircuitOpenError(RuntimeError):
    """Raised when a call is refused because the breaker is open."""


class CircuitBreaker:
    """Per-source failure breaker with a cooldown and a half-open trial."""

    def __init__(
        self,
        name: str,
        failure_threshold: int = 3,
        cooldown_seconds: float = 300.0,
    ) -> None:
        if failure_threshold < 1:
            raise ValueError("failure_threshold must be >= 1.")
        self.name = name
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds

        self._lock = threading.Lock()
        self._state = CLOSED
        self._consecutive_failures = 0
        self._opened_at: Optional[float] = None
        self.total_calls = 0
        self.total_failures = 0
        self.total_rejected = 0

    @property
    def state(self) -> str:
        """Current state, accounting for an elapsed cooldown."""
        with self._lock:
            return self._state_locked()

    def _state_locked(self) -> str:
        if self._state == OPEN and self._opened_at is not None:
            if (time.time() - self._opened_at) >= self.cooldown_seconds:
                self._state = HALF_OPEN
                logger.info("Circuit %s cooled down; admitting a trial call.", self.name)
        return self._state

    def allows_request(self) -> bool:
        """True if a call may proceed right now."""
        with self._lock:
            return self._state_locked() != OPEN

    def record_success(self) -> None:
        """Reset the breaker after a successful call."""
        with self._lock:
            if self._state != CLOSED:
                logger.info("Circuit %s recovered; closing.", self.name)
            self._state = CLOSED
            self._consecutive_failures = 0
            self._opened_at = None

    def record_failure(self) -> None:
        """Count a failure and open the breaker once the threshold is hit."""
        with self._lock:
            self.total_failures += 1
            self._consecutive_failures += 1
            if self._consecutive_failures >= self.failure_threshold:
                if self._state != OPEN:
                    logger.warning(
                        "Circuit %s opened after %d consecutive failures; "
                        "pausing this source for %.0fs.",
                        self.name, self._consecutive_failures, self.cooldown_seconds,
                    )
                self._state = OPEN
                self._opened_at = time.time()

    def call(self, fn: Callable[[], T]) -> T:
        """
        Run ``fn`` under the breaker.

        Raises ``CircuitOpenError`` without invoking ``fn`` when open.
        """
        if not self.allows_request():
            with self._lock:
                self.total_rejected += 1
            raise CircuitOpenError(
                f"Circuit {self.name} is open after repeated failures; "
                f"retry after the {self.cooldown_seconds:.0f}s cooldown."
            )

        with self._lock:
            self.total_calls += 1
        try:
            result = fn()
        except Exception:
            self.record_failure()
            raise
        self.record_success()
        return result

    def metrics(self) -> dict:
        """Telemetry snapshot for the collection audit log."""
        return {
            "name": self.name,
            "state": self.state,
            "total_calls": self.total_calls,
            "total_failures": self.total_failures,
            "total_rejected": self.total_rejected,
            "consecutive_failures": self._consecutive_failures,
            "failure_threshold": self.failure_threshold,
        }

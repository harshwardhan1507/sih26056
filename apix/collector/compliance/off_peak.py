"""
Ethical Scraper Compliance — Off-Peak Window Scheduler for APIx Tier 3 Collection.

Enforces collection restricted to off-peak Indian Standard Time (IST 02:00 to 05:00),
minimizing any load on airline or OTA consumer booking infrastructure.
"""

from __future__ import annotations

import logging
from datetime import datetime, time, timezone, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

# IST is UTC +05:30
IST_OFFSET = timedelta(hours=5, minutes=30)
IST_TZ = timezone(IST_OFFSET, name="IST")

OFF_PEAK_START = time(2, 0)   # 02:00 AM IST
OFF_PEAK_END = time(5, 0)     # 05:00 AM IST


class OffPeakWindowEnforcer:
    """
    Validates whether the current or specified time falls within the allowed
    off-peak collection window (IST 02:00 - 05:00).
    """

    def __init__(self, enforce_strictly: bool = False) -> None:
        """
        Parameters
        ----------
        enforce_strictly:
            If True, operations outside IST 02:00-05:00 raise PermissionError.
            If False (default for testing/demo), logs a warning and proceeds.
        """
        self.enforce_strictly = enforce_strictly

    @staticmethod
    def get_current_ist() -> datetime:
        """Get current timestamp in Indian Standard Time (IST)."""
        return datetime.now(timezone.utc).astimezone(IST_TZ)

    @classmethod
    def is_off_peak(cls, check_dt: Optional[datetime] = None) -> bool:
        """Check if datetime is within 02:00:00 to 05:00:00 IST."""
        dt = check_dt or cls.get_current_ist()
        if dt.tzinfo is None:
            # Treat naive datetime as IST
            dt = dt.replace(tzinfo=IST_TZ)
        else:
            dt = dt.astimezone(IST_TZ)

        t = dt.time()
        return OFF_PEAK_START <= t <= OFF_PEAK_END

    def validate_or_raise(self, check_dt: Optional[datetime] = None) -> bool:
        """
        Check off-peak window status.
        Returns True if within window, False if outside (when non-strict),
        or raises PermissionError if strictly enforced.
        """
        is_allowed = self.is_off_peak(check_dt)
        if not is_allowed:
            if self.enforce_strictly:
                raise PermissionError(
                    f"Collection blocked: current time is outside mandatory off-peak window "
                    f"({OFF_PEAK_START.strftime('%H:%M')} - {OFF_PEAK_END.strftime('%H:%M')} IST)."
                )
            # The docstring promised a warning here but nothing was emitted, so
            # out-of-window collection left no trace at all in non-strict mode.
            now_ist = (check_dt or self.get_current_ist()).strftime("%H:%M IST")
            logger.warning(
                "Collecting at %s, outside the %s-%s IST off-peak window "
                "(enforce_strictly=False, so proceeding).",
                now_ist,
                OFF_PEAK_START.strftime("%H:%M"),
                OFF_PEAK_END.strftime("%H:%M"),
            )
        return is_allowed

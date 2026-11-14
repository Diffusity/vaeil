"""The domain's only way to read the current date at this seam."""

from datetime import date, datetime
from typing import Protocol


class Clock(Protocol):
    """Port for the current local date; adapters supply the real clock."""

    def today(self) -> date:
        ...

    def now(self) -> datetime:
        """Aware UTC time for expiry; existing date-only callers still use today."""
        ...

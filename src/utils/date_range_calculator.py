"""
Date range calculation utilities for memory and mental note searches.

Provides convenience shortcuts for common time periods:
- recent/last-week: Last 7 days
- last-month: Last 30 days
- archived: Older than 30 days
"""
from datetime import datetime, timedelta
from typing import Optional, Tuple


class DateRangeCalculator:
    """Calculates date ranges from time period shortcuts."""

    @staticmethod
    def calculate(
        time_period: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        Calculate date range from time period shortcut or explicit dates.

        Args:
            time_period: Shortcut like "recent", "last-week", "last-month", "archived"
            start_date: Explicit start date (ignored if time_period provided)
            end_date: Explicit end date (ignored if time_period provided)

        Returns:
            Tuple of (start_date, end_date). Either can be None.

        Examples:
            >>> DateRangeCalculator.calculate(time_period="recent")
            (datetime(2025-11-15), datetime(2025-11-22))

            >>> DateRangeCalculator.calculate(
            ...     start_date=datetime(2025-01-01),
            ...     end_date=datetime(2025-12-31)
            ... )
            (datetime(2025-01-01), datetime(2025-12-31))
        """
        # If time_period provided, calculate from shortcuts
        if time_period:
            now = datetime.utcnow()

            if time_period in ("recent", "last-week"):
                # Last 7 days
                return (now - timedelta(days=7), now)

            elif time_period == "last-month":
                # Last 30 days
                return (now - timedelta(days=30), now)

            elif time_period == "archived":
                # Older than 30 days (no lower bound)
                return (None, now - timedelta(days=30))

            else:
                # Unknown time_period, return as-is
                return (start_date, end_date)

        # No time_period, use explicit dates
        return (start_date, end_date)

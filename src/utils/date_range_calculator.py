"""
Date range calculation utilities for memory and mental note searches.

Provides convenience shortcuts for common time periods:
- recent/last-week: Last 7 days
- last-month: Last 30 days
- archived: Older than 30 days
- last-hour: Last 1 hour
- N-hours-ago: Last N hours (e.g., "2-hours-ago")
- yesterday: Previous full day (00:00 to 23:59)
- today: Current day from 00:00 to now
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
            time_period: Shortcut like "recent", "last-week", "last-month", "archived",
                        "last-hour", "N-hours-ago", "yesterday", "today"
            start_date: Explicit start date (ignored if time_period provided)
            end_date: Explicit end date (ignored if time_period provided)

        Returns:
            Tuple of (start_date, end_date). Either can be None.

        Examples:
            >>> DateRangeCalculator.calculate(time_period="recent")
            (datetime(2025-11-15), datetime(2025-11-22))

            >>> DateRangeCalculator.calculate(time_period="2-hours-ago")
            (datetime(2025-11-22 15:00:00), datetime(2025-11-22 17:00:00))

            >>> DateRangeCalculator.calculate(time_period="yesterday")
            (datetime(2025-11-21 00:00:00), datetime(2025-11-22 00:00:00))

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

            elif time_period == "last-hour":
                # Last 1 hour
                return (now - timedelta(hours=1), now)

            elif time_period.endswith("-hours-ago"):
                # Parse "N-hours-ago" format (e.g., "2-hours-ago")
                try:
                    hours = int(time_period.split("-")[0])
                    return (now - timedelta(hours=hours), now)
                except (ValueError, IndexError):
                    # Invalid format, return as-is
                    return (start_date, end_date)

            elif time_period == "yesterday":
                # Previous full day (00:00 to 23:59:59)
                yesterday_start = (now - timedelta(days=1)).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                yesterday_end = yesterday_start + timedelta(days=1)
                return (yesterday_start, yesterday_end)

            elif time_period == "today":
                # Current day from 00:00 to now
                today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
                return (today_start, now)

            else:
                # Unknown time_period, return as-is
                return (start_date, end_date)

        # No time_period, use explicit dates
        return (start_date, end_date)

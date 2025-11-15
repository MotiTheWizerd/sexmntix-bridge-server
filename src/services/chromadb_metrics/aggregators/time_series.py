"""
Time-series aggregation utilities

Provides time-based filtering and grouping for metric data.
"""

from datetime import datetime, timedelta
from typing import List

from ..models import MetricEvent


class TimeSeriesAggregator:
    """Provides time-based aggregation and filtering"""

    @staticmethod
    def get_time_boundaries() -> dict:
        """Get common time boundary timestamps

        Returns:
            Dictionary with today_start, week_start, month_start timestamps
        """
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=now.weekday())
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        return {
            "now": now,
            "today_start": today_start,
            "week_start": week_start,
            "month_start": month_start
        }

    @staticmethod
    def filter_events_by_time(
        events: List[MetricEvent],
        start_time: datetime
    ) -> List[MetricEvent]:
        """Filter events after a specific start time

        Args:
            events: List of metric events
            start_time: Start timestamp for filtering

        Returns:
            Filtered list of events
        """
        return [e for e in events if e.timestamp >= start_time]

    @staticmethod
    def count_events_after(
        events: List[MetricEvent],
        start_time: datetime
    ) -> int:
        """Count events after a specific start time

        Args:
            events: List of metric events
            start_time: Start timestamp for filtering

        Returns:
            Count of events after start_time
        """
        return len([e for e in events if e.timestamp >= start_time])

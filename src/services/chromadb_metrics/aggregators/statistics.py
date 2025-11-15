"""
Statistical aggregation functions for metrics

Provides percentile, rate, and statistical calculations for metric data.
"""

from datetime import datetime, timedelta
from typing import List
from statistics import median as stats_median

from ..models import MetricEvent


class StatisticsAggregator:
    """Provides statistical aggregation functions for metrics"""

    @staticmethod
    def calculate_percentile(values: List[float], percentile: int) -> float:
        """Calculate percentile for a list of values

        Args:
            values: List of numeric values
            percentile: Percentile to calculate (0-100)

        Returns:
            Value at the specified percentile
        """
        if not values:
            return 0.0

        sorted_values = sorted(values)
        idx = int(len(sorted_values) * percentile / 100)
        return sorted_values[min(idx, len(sorted_values) - 1)]

    @staticmethod
    def calculate_rate(
        events: List[MetricEvent],
        window_seconds: int
    ) -> float:
        """Calculate rate (events per second) over time window

        Args:
            events: List of metric events
            window_seconds: Time window in seconds

        Returns:
            Events per second over the window
        """
        if window_seconds <= 0:
            return 0.0

        cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
        recent = [e for e in events if e.timestamp > cutoff]
        return len(recent) / window_seconds

    @staticmethod
    def calculate_average(values: List[float]) -> float:
        """Calculate average of values

        Args:
            values: List of numeric values

        Returns:
            Average value or 0.0 if empty
        """
        if not values:
            return 0.0
        return sum(values) / len(values)

    @staticmethod
    def calculate_median(values: List[float]) -> float:
        """Calculate median of values

        Args:
            values: List of numeric values

        Returns:
            Median value or 0.0 if empty
        """
        if not values:
            return 0.0
        return stats_median(values)

    @staticmethod
    def calculate_sum(values: List[float]) -> float:
        """Calculate sum of values

        Args:
            values: List of numeric values

        Returns:
            Sum of values
        """
        return sum(values) if values else 0.0

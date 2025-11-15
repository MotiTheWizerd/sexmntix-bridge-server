"""
Rate Calculator

Calculates event rates over time windows.
"""

from typing import List
from datetime import datetime, timedelta

from src.services.chromadb_metrics.models import MetricEvent


class RateCalculator:
    """Calculates event rates over time windows."""

    @staticmethod
    def calculate(events: List[MetricEvent], window_seconds: int = 60) -> float:
        """
        Calculate rate (events per second) over time window.

        Args:
            events: List of metric events
            window_seconds: Time window in seconds

        Returns:
            Event rate (events per second)
        """
        cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
        recent = [e for e in events if e.timestamp > cutoff]
        return len(recent) / window_seconds if window_seconds > 0 else 0

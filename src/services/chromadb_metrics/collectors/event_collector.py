"""
Event collector for in-memory metric storage

Manages in-memory storage of metric events, counters, and timers.
"""

from datetime import datetime
from typing import Dict, List, Any, Optional
from collections import defaultdict, deque

from ..models import MetricEvent
from ..config import MetricsConfig


class EventCollector:
    """Manages in-memory storage of metric events and counters"""

    def __init__(self, max_events: int = MetricsConfig.DEFAULT_MAX_EVENTS):
        """Initialize event collector

        Args:
            max_events: Maximum number of events to store per metric type
        """
        self.max_events = max_events

        # In-memory storage for recent events
        self.events: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_events))
        self.counters: Dict[str, int] = defaultdict(int)
        self.timers: Dict[str, List[float]] = defaultdict(list)

        # Search quality tracking
        self.search_results: deque = deque(maxlen=max_events)

    def record_event(
        self,
        metric_type: str,
        value: float,
        tags: Optional[Dict[str, Any]] = None
    ) -> MetricEvent:
        """Record a metric event

        Args:
            metric_type: Type of metric being recorded
            value: Numeric value of the metric
            tags: Optional tags/metadata for the event

        Returns:
            The created MetricEvent
        """
        event = MetricEvent(
            timestamp=datetime.utcnow(),
            metric_type=metric_type,
            value=value,
            tags=tags or {}
        )
        self.events[metric_type].append(event)
        return event

    def increment_counter(self, counter_name: str, amount: int = 1) -> int:
        """Increment a counter

        Args:
            counter_name: Name of the counter
            amount: Amount to increment by

        Returns:
            New counter value
        """
        self.counters[counter_name] += amount
        return self.counters[counter_name]

    def record_timer(self, timer_name: str, value: float) -> None:
        """Record a timing measurement

        Args:
            timer_name: Name of the timer
            value: Time value to record (typically in milliseconds)
        """
        self.timers[timer_name].append(value)

    def get_counter(self, counter_name: str) -> int:
        """Get current counter value

        Args:
            counter_name: Name of the counter

        Returns:
            Current counter value
        """
        return self.counters.get(counter_name, 0)

    def get_timer_values(self, timer_name: str) -> List[float]:
        """Get all recorded timer values

        Args:
            timer_name: Name of the timer

        Returns:
            List of recorded timer values
        """
        return self.timers.get(timer_name, [])

    def get_events(self, metric_type: str) -> List[MetricEvent]:
        """Get all events for a specific metric type

        Args:
            metric_type: Type of metric

        Returns:
            List of events for this metric type
        """
        return list(self.events.get(metric_type, []))

    def record_search_result(self, result_data: Dict[str, Any]) -> None:
        """Record search result data for quality tracking

        Args:
            result_data: Dictionary containing search result information
        """
        self.search_results.append(result_data)

    def get_search_results(self) -> List[Dict[str, Any]]:
        """Get all recorded search results

        Returns:
            List of search result data
        """
        return list(self.search_results)

    def get_all_counters(self) -> Dict[str, int]:
        """Get all counter values

        Returns:
            Dictionary of all counters
        """
        return dict(self.counters)

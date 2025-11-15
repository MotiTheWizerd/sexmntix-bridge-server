"""
Event Store

Manages in-memory storage of metric events, counters, and timers.
"""

from typing import Dict, List, Any, Optional
from collections import defaultdict, deque
from datetime import datetime

from src.services.chromadb_metrics.models import MetricEvent


class EventStore:
    """
    In-memory storage for metric events.

    Maintains:
    - Events: Time-series metric events (deques with max size)
    - Counters: Cumulative counters
    - Timers: Lists of timing values for percentile calculations
    - Search Results: Historical search result quality data
    """

    def __init__(self, max_events: int = 1000):
        """
        Initialize event store.

        Args:
            max_events: Maximum number of events per type to keep
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
    ) -> None:
        """
        Record a metric event.

        Args:
            metric_type: Type of metric
            value: Metric value
            tags: Optional tags for context
        """
        event = MetricEvent(
            timestamp=datetime.utcnow(),
            metric_type=metric_type,
            value=value,
            tags=tags or {}
        )
        self.events[metric_type].append(event)

    def increment_counter(self, counter_name: str, amount: int = 1) -> None:
        """
        Increment a counter.

        Args:
            counter_name: Name of counter
            amount: Amount to increment by
        """
        self.counters[counter_name] += amount

    def add_timer_value(self, timer_name: str, value: float) -> None:
        """
        Add a value to a timer for percentile calculations.

        Args:
            timer_name: Name of timer
            value: Timer value (milliseconds)
        """
        self.timers[timer_name].append(value)

    def add_search_result(self, result: Dict[str, Any]) -> None:
        """
        Record a search result for quality metrics.

        Args:
            result: Search result data
        """
        self.search_results.append(result)

    def get_events(self, metric_type: str) -> List[MetricEvent]:
        """Get all events of a specific type."""
        return list(self.events.get(metric_type, []))

    def get_timer_values(self, timer_name: str) -> List[float]:
        """Get all values for a timer."""
        return self.timers.get(timer_name, [])

    def get_counter(self, counter_name: str) -> int:
        """Get value of a counter."""
        return self.counters.get(counter_name, 0)

    def get_all_counters(self) -> Dict[str, int]:
        """Get all counters as a dictionary."""
        return dict(self.counters)

    def get_search_results(self) -> deque:
        """Get all recorded search results."""
        return self.search_results

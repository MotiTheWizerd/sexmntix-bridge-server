"""
Search Performance Metrics Collector

Collects search latency and performance metrics.
"""

from typing import Dict, Any
from datetime import datetime
from statistics import median

from src.modules.core import Logger
from src.services.chromadb_metrics.core.event_store import EventStore
from src.services.chromadb_metrics.calculators.percentile_calculator import PercentileCalculator
from src.services.chromadb_metrics.calculators.rate_calculator import RateCalculator


class SearchPerformanceCollector:
    """Collects search performance metrics."""

    def __init__(
        self,
        event_store: EventStore,
        percentile_calc: PercentileCalculator,
        rate_calc: RateCalculator,
        logger: Logger
    ):
        """
        Initialize collector.

        Args:
            event_store: Event store with metrics
            percentile_calc: Percentile calculator
            rate_calc: Rate calculator
            logger: Logger instance
        """
        self.event_store = event_store
        self.percentile_calc = percentile_calc
        self.rate_calc = rate_calc
        self.logger = logger

    async def collect(self) -> Dict[str, Any]:
        """
        Get search performance metrics.

        Returns:
            Dictionary with search performance metrics
        """
        search_latencies = self.event_store.get_timer_values("search_latency")

        if not search_latencies:
            return {
                "avg_search_latency": 0,
                "p50_search_latency": 0,
                "p95_search_latency": 0,
                "p99_search_latency": 0,
                "searches_today": 0,
                "slow_searches": 0,
            }

        # Calculate time-based metrics
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        events = self.event_store.get_events("vector.searched")
        searches_today = len([
            e for e in events
            if e.timestamp >= today_start
        ])

        return {
            "avg_search_latency": round(sum(search_latencies) / len(search_latencies), 2),
            "median_search_latency": round(median(search_latencies), 2),
            "p50_search_latency": round(self.percentile_calc.calculate(search_latencies, 50), 2),
            "p95_search_latency": round(self.percentile_calc.calculate(search_latencies, 95), 2),
            "p99_search_latency": round(self.percentile_calc.calculate(search_latencies, 99), 2),
            "searches_today": searches_today,
            "searches_total": self.event_store.get_counter("searches_total"),
            "slow_searches": self.event_store.get_counter("slow_searches"),
            "searches_per_hour": round(self.rate_calc.calculate(events, window_seconds=3600), 2),
        }

"""
Search metrics collector

Gathers search performance and quality metrics.
"""

from typing import Dict, Any, List
from ..collectors.event_collector import EventCollector
from ..aggregators.statistics import StatisticsAggregator
from ..aggregators.time_series import TimeSeriesAggregator
from ..config import MetricsConfig


class SearchMetricsCollector:
    """Collects search performance and quality metrics"""

    def __init__(self, event_collector: EventCollector):
        """Initialize search metrics collector

        Args:
            event_collector: Event collector instance
        """
        self.event_collector = event_collector
        self.stats = StatisticsAggregator()
        self.time_series = TimeSeriesAggregator()

    async def get_search_performance_metrics(self) -> Dict[str, Any]:
        """Get search performance metrics

        Returns:
            Dictionary with latency statistics and search counts
        """
        search_latencies = self.event_collector.get_timer_values(MetricsConfig.TIMER_SEARCH_LATENCY)

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
        time_boundaries = self.time_series.get_time_boundaries()
        search_events = self.event_collector.get_events(MetricsConfig.EVENT_VECTOR_SEARCHED)

        searches_today = self.time_series.count_events_after(
            search_events,
            time_boundaries["today_start"]
        )

        return {
            "avg_search_latency": round(self.stats.calculate_average(search_latencies), 2),
            "median_search_latency": round(self.stats.calculate_median(search_latencies), 2),
            "p50_search_latency": round(self.stats.calculate_percentile(search_latencies, 50), 2),
            "p95_search_latency": round(self.stats.calculate_percentile(search_latencies, 95), 2),
            "p99_search_latency": round(self.stats.calculate_percentile(search_latencies, 99), 2),
            "searches_today": searches_today,
            "searches_total": self.event_collector.get_counter(MetricsConfig.COUNTER_SEARCHES_TOTAL),
            "slow_searches": self.event_collector.get_counter(MetricsConfig.COUNTER_SLOW_SEARCHES),
            "searches_per_hour": round(
                self.stats.calculate_rate(search_events, MetricsConfig.TIME_WINDOW_HOUR),
                2
            ),
        }

    async def get_search_quality_metrics(self) -> Dict[str, Any]:
        """Get search quality metrics

        Returns:
            Dictionary with similarity scores and result quality stats
        """
        search_results = self.event_collector.get_search_results()

        if not search_results:
            return {
                "avg_similarity": 0,
                "searches_no_results": 0,
                "similarity_distribution": {
                    "high": 0,
                    "medium": 0,
                    "low": 0,
                    "very_low": 0,
                }
            }

        # Calculate average similarity
        all_similarities = []
        for result in search_results:
            all_similarities.extend(result["similarities"])

        avg_similarity = self.stats.calculate_average(all_similarities)
        median_similarity = self.stats.calculate_median(all_similarities)

        # Calculate average results returned
        avg_results = self.stats.calculate_average([
            r["result_count"] for r in search_results
        ])

        no_results_count = self.event_collector.get_counter(MetricsConfig.COUNTER_NO_RESULTS)
        no_results_rate = (no_results_count / max(len(search_results), 1)) * 100

        return {
            "avg_similarity": round(avg_similarity, 3),
            "median_similarity": round(median_similarity, 3),
            "avg_results_returned": round(avg_results, 2),
            "searches_no_results": no_results_count,
            "searches_no_results_rate": round(no_results_rate, 2),
            "similarity_distribution": {
                "high": self.event_collector.get_counter(MetricsConfig.COUNTER_SIMILARITY_HIGH),
                "medium": self.event_collector.get_counter(MetricsConfig.COUNTER_SIMILARITY_MEDIUM),
                "low": self.event_collector.get_counter(MetricsConfig.COUNTER_SIMILARITY_LOW),
                "very_low": self.event_collector.get_counter(MetricsConfig.COUNTER_SIMILARITY_VERY_LOW),
            }
        }

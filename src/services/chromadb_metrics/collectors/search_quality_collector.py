"""
Search Quality Metrics Collector

Collects search quality and similarity metrics.
"""

from typing import Dict, Any
from statistics import median

from src.modules.core import Logger
from src.services.chromadb_metrics.core.event_store import EventStore


class SearchQualityCollector:
    """Collects search quality metrics."""

    def __init__(self, event_store: EventStore, logger: Logger):
        """
        Initialize collector.

        Args:
            event_store: Event store with metrics
            logger: Logger instance
        """
        self.event_store = event_store
        self.logger = logger

    async def collect(self) -> Dict[str, Any]:
        """
        Get search quality metrics.

        Returns:
            Dictionary with search quality metrics
        """
        search_results = self.event_store.get_search_results()

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

        avg_similarity = sum(all_similarities) / len(all_similarities) if all_similarities else 0

        # Calculate average results returned
        avg_results = sum(r["result_count"] for r in search_results) / len(search_results)

        return {
            "avg_similarity": round(avg_similarity, 3),
            "median_similarity": round(median(all_similarities), 3) if all_similarities else 0,
            "avg_results_returned": round(avg_results, 2),
            "searches_no_results": self.event_store.get_counter("searches_no_results"),
            "searches_no_results_rate": round(
                self.event_store.get_counter("searches_no_results") / max(len(search_results), 1) * 100, 2
            ),
            "similarity_distribution": {
                "high": self.event_store.get_counter("similarity_high"),
                "medium": self.event_store.get_counter("similarity_medium"),
                "low": self.event_store.get_counter("similarity_low"),
                "very_low": self.event_store.get_counter("similarity_very_low"),
            }
        }

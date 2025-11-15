"""
Event handlers for ChromaDB metrics

Handles EventBus events and updates metrics collectors.
"""

from datetime import datetime
from typing import Dict, Any

from src.modules.core import EventBus, Logger
from ..collectors.event_collector import EventCollector
from ..config import MetricsConfig


class MetricsEventHandlers:
    """Handles EventBus events for metrics collection"""

    def __init__(
        self,
        event_bus: EventBus,
        event_collector: EventCollector,
        logger: Logger
    ):
        """Initialize event handlers

        Args:
            event_bus: Event bus for subscribing to events
            event_collector: Event collector for storing metrics
            logger: Logger instance
        """
        self.event_bus = event_bus
        self.event_collector = event_collector
        self.logger = logger

    def register_handlers(self) -> None:
        """Subscribe to ChromaDB-related events"""
        self.event_bus.subscribe(MetricsConfig.EVENT_VECTOR_STORED, self._on_vector_stored)
        self.event_bus.subscribe(MetricsConfig.EVENT_VECTOR_SEARCHED, self._on_vector_searched)
        self.event_bus.subscribe(MetricsConfig.EVENT_SEARCH_COMPLETED, self._on_search_completed)
        self.event_bus.subscribe(MetricsConfig.EVENT_CHROMADB_ERROR, self._on_chromadb_error)

    async def _on_vector_stored(self, data: Dict[str, Any]) -> None:
        """Track vector storage operations

        Args:
            data: Event data with user_id, project_id, collection_name
        """
        self.event_collector.record_event(
            metric_type=MetricsConfig.EVENT_VECTOR_STORED,
            value=1,
            tags={
                "user_id": data.get("user_id"),
                "project_id": data.get("project_id"),
                "collection": data.get("collection_name"),
            }
        )
        self.event_collector.increment_counter(MetricsConfig.COUNTER_VECTORS_STORED)

    async def _on_vector_searched(self, data: Dict[str, Any]) -> None:
        """Track vector search operations

        Args:
            data: Event data with duration_ms, user_id, project_id, etc.
        """
        duration_ms = data.get("duration_ms", 0)

        self.event_collector.record_event(
            metric_type=MetricsConfig.EVENT_VECTOR_SEARCHED,
            value=duration_ms,
            tags={
                "user_id": data.get("user_id"),
                "project_id": data.get("project_id"),
                "collection": data.get("collection_name"),
                "collection_size": data.get("collection_size", 0),
            }
        )

        self.event_collector.record_timer(MetricsConfig.TIMER_SEARCH_LATENCY, duration_ms)
        self.event_collector.increment_counter(MetricsConfig.COUNTER_SEARCHES_TOTAL)

        # Track slow searches (>500ms)
        if duration_ms > MetricsConfig.SLOW_SEARCH_THRESHOLD_MS:
            self.event_collector.increment_counter(MetricsConfig.COUNTER_SLOW_SEARCHES)

    async def _on_search_completed(self, data: Dict[str, Any]) -> None:
        """Track search quality metrics

        Args:
            data: Event data with results and query
        """
        results = data.get("results", [])
        query = data.get("query", "")

        if not results:
            self.event_collector.increment_counter(MetricsConfig.COUNTER_NO_RESULTS)

        # Calculate average similarity
        if results:
            similarities = [r.get("similarity", 0) for r in results]
            avg_similarity = sum(similarities) / len(similarities)

            self.event_collector.record_search_result({
                "timestamp": datetime.utcnow(),
                "query": query[:100],
                "result_count": len(results),
                "avg_similarity": avg_similarity,
                "similarities": similarities,
            })

            # Track similarity distribution
            for sim in similarities:
                if sim >= MetricsConfig.SIMILARITY_HIGH_THRESHOLD:
                    self.event_collector.increment_counter(MetricsConfig.COUNTER_SIMILARITY_HIGH)
                elif sim >= MetricsConfig.SIMILARITY_MEDIUM_THRESHOLD:
                    self.event_collector.increment_counter(MetricsConfig.COUNTER_SIMILARITY_MEDIUM)
                elif sim >= MetricsConfig.SIMILARITY_LOW_THRESHOLD:
                    self.event_collector.increment_counter(MetricsConfig.COUNTER_SIMILARITY_LOW)
                else:
                    self.event_collector.increment_counter(MetricsConfig.COUNTER_SIMILARITY_VERY_LOW)

    async def _on_chromadb_error(self, data: Dict[str, Any]) -> None:
        """Track ChromaDB errors

        Args:
            data: Event data with error information
        """
        self.event_collector.increment_counter(MetricsConfig.COUNTER_ERRORS)
        self.logger.error(f"ChromaDB error: {data.get('error')}")

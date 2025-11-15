"""
Event Handlers

Handles EventBus subscriptions and processes metric events.
"""

from typing import Dict, Any
from datetime import datetime

from src.modules.core import EventBus, Logger
from src.services.chromadb_metrics.core.event_store import EventStore


class EventHandlers:
    """
    Subscribes to and processes ChromaDB-related events.

    Handles:
    - Vector storage operations
    - Vector search operations
    - Search quality metrics
    - ChromaDB errors
    """

    def __init__(self, event_bus: EventBus, event_store: EventStore, logger: Logger):
        """
        Initialize event handlers.

        Args:
            event_bus: EventBus for subscribing to events
            event_store: EventStore for recording metrics
            logger: Logger instance
        """
        self.event_bus = event_bus
        self.event_store = event_store
        self.logger = logger

        # Register event handlers
        self._register_handlers()

    def _register_handlers(self):
        """Subscribe to ChromaDB-related events"""
        self.event_bus.subscribe("vector.stored", self._on_vector_stored)
        self.event_bus.subscribe("vector.searched", self._on_vector_searched)
        self.event_bus.subscribe("search.completed", self._on_search_completed)
        self.event_bus.subscribe("chromadb.error", self._on_chromadb_error)

    async def _on_vector_stored(self, data: Dict[str, Any]):
        """Track vector storage operations"""
        self.event_store.record_event(
            metric_type="vector.stored",
            value=1,
            tags={
                "user_id": data.get("user_id"),
                "project_id": data.get("project_id"),
                "collection": data.get("collection_name"),
            }
        )
        self.event_store.increment_counter("vectors_stored_total")

    async def _on_vector_searched(self, data: Dict[str, Any]):
        """Track vector search operations"""
        duration_ms = data.get("duration_ms", 0)

        self.event_store.record_event(
            metric_type="vector.searched",
            value=duration_ms,
            tags={
                "user_id": data.get("user_id"),
                "project_id": data.get("project_id"),
                "collection": data.get("collection_name"),
                "collection_size": data.get("collection_size", 0),
            }
        )

        self.event_store.add_timer_value("search_latency", duration_ms)
        self.event_store.increment_counter("searches_total")

        # Track slow searches (>500ms)
        if duration_ms > 500:
            self.event_store.increment_counter("slow_searches")

    async def _on_search_completed(self, data: Dict[str, Any]):
        """Track search quality metrics"""
        results = data.get("results", [])
        query = data.get("query", "")

        if not results:
            self.event_store.increment_counter("searches_no_results")

        # Calculate average similarity
        if results:
            similarities = [r.get("similarity", 0) for r in results]
            avg_similarity = sum(similarities) / len(similarities)

            self.event_store.add_search_result({
                "timestamp": datetime.utcnow(),
                "query": query[:100],
                "result_count": len(results),
                "avg_similarity": avg_similarity,
                "similarities": similarities,
            })

            # Track similarity distribution
            for sim in similarities:
                if sim >= 0.8:
                    self.event_store.increment_counter("similarity_high")
                elif sim >= 0.5:
                    self.event_store.increment_counter("similarity_medium")
                elif sim >= 0.3:
                    self.event_store.increment_counter("similarity_low")
                else:
                    self.event_store.increment_counter("similarity_very_low")

    async def _on_chromadb_error(self, data: Dict[str, Any]):
        """Track ChromaDB errors"""
        self.event_store.increment_counter("chromadb_errors")
        self.logger.error(f"ChromaDB error: {data.get('error')}")

"""
Telemetry and Event Publishing

Single Responsibility: Handle logging and event publishing for search operations.

This module centralizes all telemetry concerns, making it easier to modify
logging behavior and event formats without touching core business logic.
"""

from typing import List, Dict, Any
from src.modules.core import EventBus, Logger
from .models import SearchRequest, SearchResponse


class SearchTelemetry:
    """
    Manages telemetry and event publishing for search operations.

    Provides centralized logging and event publishing to keep the main
    handler class focused on orchestration logic.
    """

    def __init__(self, event_bus: EventBus, logger: Logger):
        """
        Initialize telemetry handler.

        Args:
            event_bus: Event bus for publishing events
            logger: Logger instance
        """
        self.event_bus = event_bus
        self.logger = logger

    def log_search_start(self, request: SearchRequest) -> None:
        """
        Log the start of a search operation.

        Args:
            request: The search request being processed
        """
        self.logger.info(
            f"Searching memories for query: '{request.query[:100]}...' "
            f"(user: {request.user_id}, project: {request.project_id})"
        )

    def log_embedding_generated(self, dimensions: int, cached: bool) -> None:
        """
        Log embedding generation completion.

        Args:
            dimensions: Number of embedding dimensions
            cached: Whether the embedding was retrieved from cache
        """
        self.logger.info(
            f"Generated query embedding: {dimensions} dimensions, cached: {cached}"
        )

    def log_chromadb_search(
        self,
        user_id: str,
        project_id: str,
        limit: int,
        where_filter: Dict[str, Any],
        results_count: int
    ) -> None:
        """
        Log ChromaDB search operation.

        Args:
            user_id: User identifier
            project_id: Project identifier
            limit: Maximum results requested
            where_filter: Metadata filter applied
            results_count: Number of results returned
        """
        self.logger.info(
            f"Searching ChromaDB for user_id={user_id}, project_id={project_id}, "
            f"limit={limit}, where_filter={where_filter}"
        )
        self.logger.info(f"ChromaDB returned {results_count} results before filtering")

    def log_temporal_decay(self, enabled: bool, half_life_days: float) -> None:
        """
        Log temporal decay application.

        Args:
            enabled: Whether temporal decay was enabled
            half_life_days: Half-life setting used
        """
        self.logger.info(
            f"Temporal decay {'applied' if enabled else 'skipped'} "
            f"(half_life: {half_life_days} days)"
        )

    def log_search_completion(
        self,
        results_count: int,
        duration_ms: float,
        min_similarity: float,
        cached: bool,
        collection_size: int
    ) -> None:
        """
        Log search completion with summary.

        Args:
            results_count: Number of results returned
            duration_ms: Total duration in milliseconds
            min_similarity: Minimum similarity threshold
            cached: Whether query embedding was cached
            collection_size: Size of the collection
        """
        self.logger.info(
            f"Found {results_count} memories in {duration_ms:.2f}ms "
            f"(min_similarity: {min_similarity}, cached: {cached}, "
            f"collection_size: {collection_size})"
        )

    def publish_vector_searched_event(self, response: SearchResponse) -> None:
        """
        Publish vector.searched event with performance metrics.

        Args:
            response: The search response containing all metadata
        """
        self.event_bus.publish("vector.searched", {
            "query": response.query,
            "user_id": response.user_id,
            "project_id": response.project_id,
            "results_count": response.results_count,
            "query_cached": response.query_cached,
            "temporal_decay_enabled": response.temporal_decay_enabled,
            "half_life_days": response.half_life_days,
            "duration_ms": response.duration_ms,
            "collection_size": response.collection_size,
        })

    def publish_search_completed_event(self, response: SearchResponse) -> None:
        """
        Publish search.completed event with quality metrics.

        Args:
            response: The search response containing results
        """
        self.event_bus.publish("search.completed", {
            "query": response.query,
            "results": response.results,
            "user_id": response.user_id,
            "project_id": response.project_id,
        })

    def publish_all_events(self, response: SearchResponse) -> None:
        """
        Publish all search-related events.

        Convenience method to publish all events at once.

        Args:
            response: The search response
        """
        self.publish_vector_searched_event(response)
        self.publish_search_completed_event(response)

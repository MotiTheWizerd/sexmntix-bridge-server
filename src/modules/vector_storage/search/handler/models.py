"""
Search Request/Response Models

Single Responsibility: Define data structures for search operations.

This module provides strongly-typed models for search requests and responses,
improving type safety and making the API more explicit.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List


@dataclass
class SearchRequest:
    """
    Encapsulates all parameters for a similarity search request.

    This model provides a single, well-defined structure for search parameters,
    making the API more maintainable and easier to test.
    """

    query: str
    user_id: str
    project_id: str
    limit: int = 10
    where_filter: Optional[Dict[str, Any]] = None
    min_similarity: float = 0.0
    enable_temporal_decay: bool = False
    half_life_days: float = 30.0

    def __post_init__(self):
        """Validate search request parameters."""
        if not self.query:
            raise ValueError("Query cannot be empty")
        if not self.user_id:
            raise ValueError("User ID cannot be empty")
        if not self.project_id:
            raise ValueError("Project ID cannot be empty")
        if self.limit <= 0:
            raise ValueError(f"Limit must be positive, got {self.limit}")
        if not 0.0 <= self.min_similarity <= 1.0:
            raise ValueError(f"min_similarity must be between 0.0 and 1.0, got {self.min_similarity}")
        if self.half_life_days <= 0:
            raise ValueError(f"half_life_days must be positive, got {self.half_life_days}")


@dataclass
class SearchResponse:
    """
    Encapsulates search results with metadata.

    Includes performance metrics and context information that can be
    useful for debugging, monitoring, and optimization.
    """

    results: List[Dict[str, Any]]
    query: str
    user_id: str
    project_id: str
    results_count: int
    duration_ms: float
    collection_size: int
    query_cached: bool
    temporal_decay_enabled: bool
    half_life_days: Optional[float] = None

    @classmethod
    def from_search_results(
        cls,
        results: List[Dict[str, Any]],
        request: SearchRequest,
        duration_ms: float,
        collection_size: int,
        query_cached: bool
    ) -> "SearchResponse":
        """
        Create a SearchResponse from search results and request context.

        Args:
            results: List of search result dictionaries
            request: The original search request
            duration_ms: Search operation duration in milliseconds
            collection_size: Total number of vectors in collection
            query_cached: Whether the query embedding was cached

        Returns:
            Constructed SearchResponse instance
        """
        return cls(
            results=results,
            query=request.query[:100],  # Truncate for logging
            user_id=request.user_id,
            project_id=request.project_id,
            results_count=len(results),
            duration_ms=duration_ms,
            collection_size=collection_size,
            query_cached=query_cached,
            temporal_decay_enabled=request.enable_temporal_decay,
            half_life_days=request.half_life_days if request.enable_temporal_decay else None
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary format for serialization."""
        return {
            "results": self.results,
            "query": self.query,
            "user_id": self.user_id,
            "project_id": self.project_id,
            "results_count": self.results_count,
            "duration_ms": self.duration_ms,
            "collection_size": self.collection_size,
            "query_cached": self.query_cached,
            "temporal_decay_enabled": self.temporal_decay_enabled,
            "half_life_days": self.half_life_days
        }

"""
Memory Search Request DTO

Data transfer object for semantic search requests.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from .threshold_preset import ThresholdPreset


@dataclass
class MemorySearchRequest:
    """
    Request parameters for semantic memory search.

    Attributes:
        query: Search query text
        user_id: User identifier for collection isolation
        project_id: Project identifier for collection isolation
        limit: Maximum number of results to return
        where_filter: Optional metadata filter (ChromaDB where syntax)
        min_similarity: Minimum similarity threshold (0.0 to 1.0)
        enable_temporal_decay: Apply exponential decay based on memory age
        half_life_days: Half-life in days for exponential decay
        enable_hybrid_search: Enable hybrid search (70% vector + 30% keyword)
        threshold_preset: Use preset threshold (overrides min_similarity if set)
    """

    query: str
    """Search query text"""

    user_id: str
    """User identifier for collection isolation"""

    project_id: str
    """Project identifier for collection isolation"""

    limit: int = 10
    """Maximum number of results to return"""

    where_filter: Optional[Dict[str, Any]] = None
    """Optional metadata filter (ChromaDB where syntax)"""

    min_similarity: float = 0.0
    """Minimum similarity threshold (0.0 to 1.0)"""

    enable_temporal_decay: bool = False
    """Apply exponential decay based on memory age"""

    half_life_days: float = 30.0
    """Half-life in days for exponential decay"""

    enable_hybrid_search: bool = False
    """Enable hybrid search combining vector similarity (70%) + keyword matching (30%)"""

    threshold_preset: Optional[ThresholdPreset] = None
    """Use preset threshold (overrides min_similarity if set)"""

    def __post_init__(self):
        """Validate request parameters and apply threshold preset if set."""
        if not self.query or not self.query.strip():
            raise ValueError("Query cannot be empty")

        if not self.user_id or not self.user_id.strip():
            raise ValueError("user_id cannot be empty")

        if not self.project_id or not self.project_id.strip():
            raise ValueError("project_id cannot be empty")

        # Apply threshold preset if specified (overrides min_similarity)
        if self.threshold_preset is not None:
            self.min_similarity = self.threshold_preset.threshold

        if not (0.0 <= self.min_similarity <= 1.0):
            raise ValueError(
                f"min_similarity must be between 0.0 and 1.0, got {self.min_similarity}"
            )

        if self.limit < 1:
            raise ValueError(f"limit must be at least 1, got {self.limit}")

        if self.half_life_days <= 0:
            raise ValueError(
                f"half_life_days must be positive, got {self.half_life_days}"
            )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "query": self.query,
            "user_id": self.user_id,
            "project_id": self.project_id,
            "limit": self.limit,
            "where_filter": self.where_filter,
            "min_similarity": self.min_similarity,
            "enable_temporal_decay": self.enable_temporal_decay,
            "half_life_days": self.half_life_days,
            "enable_hybrid_search": self.enable_hybrid_search,
            "threshold_preset": self.threshold_preset.value if self.threshold_preset else None,
        }

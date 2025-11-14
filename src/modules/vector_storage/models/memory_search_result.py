"""
Memory Search Result DTO

Data transfer object for semantic search results.
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional
from datetime import datetime


@dataclass
class MemorySearchResult:
    """
    Single memory result from semantic search.

    Attributes:
        id: Memory identifier
        document: Full memory JSON document
        metadata: Flat metadata dictionary
        similarity: Similarity score (0.0 to 1.0)
        distance: L2 distance from query (0.0 to ~2.0)
        original_similarity: Similarity before temporal decay (if applied)
        decay_factor: Applied decay multiplier (if temporal decay enabled)
        age_days: Age of memory in days (if temporal decay enabled)
    """

    id: str
    """Memory identifier"""

    document: Dict[str, Any]
    """Full memory JSON document"""

    metadata: Dict[str, Any]
    """Flat metadata dictionary"""

    similarity: float
    """Similarity score (0.0 to 1.0)"""

    distance: float
    """L2 distance from query (0.0 to ~2.0)"""

    original_similarity: Optional[float] = None
    """Similarity before temporal decay (if applied)"""

    decay_factor: Optional[float] = None
    """Applied decay multiplier (if temporal decay enabled)"""

    age_days: Optional[float] = None
    """Age of memory in days (if temporal decay enabled)"""

    def __post_init__(self):
        """Validate result data."""
        if not self.id or not self.id.strip():
            raise ValueError("id cannot be empty")

        if not (0.0 <= self.similarity <= 1.0):
            raise ValueError(
                f"similarity must be between 0.0 and 1.0, got {self.similarity}"
            )

        if self.distance < 0:
            raise ValueError(f"distance cannot be negative, got {self.distance}")

        if self.original_similarity is not None:
            if not (0.0 <= self.original_similarity <= 1.0):
                raise ValueError(
                    f"original_similarity must be between 0.0 and 1.0, got {self.original_similarity}"
                )

        if self.decay_factor is not None:
            if not (0.0 <= self.decay_factor <= 1.0):
                raise ValueError(
                    f"decay_factor must be between 0.0 and 1.0, got {self.decay_factor}"
                )

        if self.age_days is not None:
            if self.age_days < 0:
                raise ValueError(f"age_days cannot be negative, got {self.age_days}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = {
            "id": self.id,
            "document": self.document,
            "metadata": self.metadata,
            "similarity": self.similarity,
            "distance": self.distance,
        }

        # Add optional fields if present
        if self.original_similarity is not None:
            result["original_similarity"] = self.original_similarity

        if self.decay_factor is not None:
            result["decay_factor"] = self.decay_factor

        if self.age_days is not None:
            result["age_days"] = self.age_days

        return result

    @classmethod
    def from_search_result(
        cls,
        search_result,  # SearchResult from infrastructure
        original_similarity: Optional[float] = None,
        decay_factor: Optional[float] = None,
        age_days: Optional[float] = None,
    ) -> "MemorySearchResult":
        """
        Create MemorySearchResult from infrastructure SearchResult.

        Args:
            search_result: SearchResult instance from infrastructure layer
            original_similarity: Original similarity before decay (if temporal decay applied)
            decay_factor: Decay factor applied (if temporal decay enabled)
            age_days: Age in days (if temporal decay enabled)

        Returns:
            MemorySearchResult instance
        """
        return cls(
            id=search_result.id,
            document=search_result.document,
            metadata=search_result.metadata,
            similarity=search_result.similarity,
            distance=search_result.distance,
            original_similarity=original_similarity,
            decay_factor=decay_factor,
            age_days=age_days,
        )

"""
Memory Search Result Model

Core dataclass for memory search results with delegated validation and serialization.
"""

from dataclasses import dataclass
from typing import Dict, Any, Optional
from .validators import validate_search_result
from .serializers import serialize_to_dict


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
        """Validate result data using validators module."""
        validate_search_result(
            id_value=self.id,
            similarity=self.similarity,
            distance=self.distance,
            original_similarity=self.original_similarity,
            decay_factor=self.decay_factor,
            age_days=self.age_days
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary representation.

        Uses serializers module for conversion logic.

        Returns:
            Dictionary representation of the result
        """
        return serialize_to_dict(self)

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

        Uses factory module for creation logic.

        Args:
            search_result: SearchResult instance from infrastructure layer
            original_similarity: Original similarity before decay (if temporal decay applied)
            decay_factor: Decay factor applied (if temporal decay enabled)
            age_days: Age in days (if temporal decay enabled)

        Returns:
            MemorySearchResult instance
        """
        from .factory import from_search_result
        return from_search_result(search_result, original_similarity, decay_factor, age_days)

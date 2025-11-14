"""
Search Result Model

Represents a single search result with similarity scoring and metadata.
"""

from typing import Dict, Any


class SearchResult:
    """
    Search result with similarity scoring.

    Attributes:
        id: Memory identifier
        document: Full memory JSON
        metadata: Flat metadata dict
        distance: L2 distance from query
        similarity: Similarity percentage (0-100%)
    """

    def __init__(
        self,
        id: str,
        document: Dict[str, Any],
        metadata: Dict[str, Any],
        distance: float
    ):
        self.id = id
        self.document = document
        self.metadata = metadata
        self.distance = distance
        self.similarity = self._calculate_similarity(distance)

    @staticmethod
    def _calculate_similarity(distance: float) -> float:
        """
        Convert L2 distance to similarity percentage.

        L2 distance range: 0 to ~2.0
        - 0.0 = identical vectors (100% similarity)
        - 2.0 = completely different (0% similarity)

        Formula: similarity = max(0, 1.0 - (distance / 2.0))

        Args:
            distance: L2 distance from ChromaDB

        Returns:
            Similarity score between 0.0 and 1.0
        """
        return max(0.0, 1.0 - (distance / 2.0))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "document": self.document,
            "metadata": self.metadata,
            "distance": self.distance,
            "similarity": self.similarity
        }

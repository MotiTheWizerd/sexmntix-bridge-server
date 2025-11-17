"""
Factory methods for Memory Search Result

Utilities for creating MemorySearchResult instances from various sources.
"""

from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .model import MemorySearchResult


def from_search_result(
    search_result,  # SearchResult from infrastructure layer
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
    from .model import MemorySearchResult

    return MemorySearchResult(
        id=search_result.id,
        document=search_result.document,
        metadata=search_result.metadata,
        similarity=search_result.similarity,
        distance=search_result.distance,
        original_similarity=original_similarity,
        decay_factor=decay_factor,
        age_days=age_days,
    )


def from_dict(data: Dict[str, Any]) -> "MemorySearchResult":
    """
    Create MemorySearchResult from dictionary.

    Args:
        data: Dictionary containing result fields

    Returns:
        MemorySearchResult instance

    Raises:
        KeyError: If required fields are missing
        ValueError: If field values are invalid
    """
    from .model import MemorySearchResult

    return MemorySearchResult(
        id=data["id"],
        document=data["document"],
        metadata=data["metadata"],
        similarity=data["similarity"],
        distance=data["distance"],
        original_similarity=data.get("original_similarity"),
        decay_factor=data.get("decay_factor"),
        age_days=data.get("age_days"),
    )


def from_chroma_result(
    chroma_id: str,
    chroma_document: str,
    chroma_metadata: Dict[str, Any],
    chroma_distance: float,
    similarity_score: float,
) -> "MemorySearchResult":
    """
    Create MemorySearchResult directly from ChromaDB query result.

    Args:
        chroma_id: ID from ChromaDB
        chroma_document: Document JSON string from ChromaDB
        chroma_metadata: Metadata dict from ChromaDB
        chroma_distance: L2 distance from ChromaDB
        similarity_score: Calculated similarity score

    Returns:
        MemorySearchResult instance
    """
    from .model import MemorySearchResult
    import json

    # Parse document if it's a JSON string
    document = json.loads(chroma_document) if isinstance(chroma_document, str) else chroma_document

    return MemorySearchResult(
        id=chroma_id,
        document=document,
        metadata=chroma_metadata,
        similarity=similarity_score,
        distance=chroma_distance,
    )


def create_batch(search_results: list, **kwargs) -> list["MemorySearchResult"]:
    """
    Create a list of MemorySearchResult from infrastructure SearchResults.

    Args:
        search_results: List of SearchResult instances
        **kwargs: Additional arguments passed to each from_search_result call

    Returns:
        List of MemorySearchResult instances
    """
    return [from_search_result(result, **kwargs) for result in search_results]

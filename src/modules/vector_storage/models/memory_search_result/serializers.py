"""
Serializers for Memory Search Result

Utilities for converting memory search results to different formats.
"""

from typing import Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .model import MemorySearchResult


def serialize_core_fields(result: "MemorySearchResult") -> Dict[str, Any]:
    """
    Serialize core fields of a memory search result.

    Args:
        result: MemorySearchResult instance

    Returns:
        Dictionary with core fields (always present)
    """
    return {
        "id": result.id,
        "document": result.document,
        "metadata": result.metadata,
        "similarity": result.similarity,
        "distance": result.distance,
    }


def serialize_optional_fields(result: "MemorySearchResult") -> Dict[str, Any]:
    """
    Serialize optional fields of a memory search result.

    Only includes fields that are not None.

    Args:
        result: MemorySearchResult instance

    Returns:
        Dictionary with optional fields (only if present)
    """
    optional = {}

    if result.original_similarity is not None:
        optional["original_similarity"] = result.original_similarity

    if result.decay_factor is not None:
        optional["decay_factor"] = result.decay_factor

    if result.age_days is not None:
        optional["age_days"] = result.age_days

    return optional


def serialize_to_dict(result: "MemorySearchResult") -> Dict[str, Any]:
    """
    Convert memory search result to dictionary representation.

    Args:
        result: MemorySearchResult instance

    Returns:
        Complete dictionary representation
    """
    data = serialize_core_fields(result)
    data.update(serialize_optional_fields(result))
    return data


def serialize_minimal(result: "MemorySearchResult") -> Dict[str, Any]:
    """
    Serialize result with minimal information (no document/metadata).

    Useful for lightweight responses or logging.

    Args:
        result: MemorySearchResult instance

    Returns:
        Dictionary with minimal fields
    """
    minimal = {
        "id": result.id,
        "similarity": result.similarity,
        "distance": result.distance,
    }

    # Add optional fields if present
    minimal.update(serialize_optional_fields(result))

    return minimal


def serialize_batch(results: list["MemorySearchResult"]) -> list[Dict[str, Any]]:
    """
    Serialize a list of memory search results.

    Args:
        results: List of MemorySearchResult instances

    Returns:
        List of dictionaries
    """
    return [serialize_to_dict(result) for result in results]

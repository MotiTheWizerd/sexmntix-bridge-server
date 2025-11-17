"""
Validators for Memory Search Result

Reusable validation utilities for memory search result fields.
All validators raise ValueError on invalid input.
"""

from typing import Optional


def validate_id(id_value: str) -> None:
    """
    Validate memory ID is not empty.

    Args:
        id_value: Memory identifier

    Raises:
        ValueError: If ID is empty or whitespace-only
    """
    if not id_value or not id_value.strip():
        raise ValueError("id cannot be empty")


def validate_similarity(value: float, field_name: str = "similarity") -> None:
    """
    Validate similarity score is between 0.0 and 1.0.

    Args:
        value: Similarity score to validate
        field_name: Name of field for error message

    Raises:
        ValueError: If value is not in valid range
    """
    if not (0.0 <= value <= 1.0):
        raise ValueError(
            f"{field_name} must be between 0.0 and 1.0, got {value}"
        )


def validate_distance(distance: float) -> None:
    """
    Validate distance is non-negative.

    Args:
        distance: L2 distance value

    Raises:
        ValueError: If distance is negative
    """
    if distance < 0:
        raise ValueError(f"distance cannot be negative, got {distance}")


def validate_decay_factor(factor: Optional[float]) -> None:
    """
    Validate decay factor is between 0.0 and 1.0 (if provided).

    Args:
        factor: Decay factor to validate (can be None)

    Raises:
        ValueError: If factor is provided but not in valid range
    """
    if factor is not None:
        if not (0.0 <= factor <= 1.0):
            raise ValueError(
                f"decay_factor must be between 0.0 and 1.0, got {factor}"
            )


def validate_age_days(days: Optional[float]) -> None:
    """
    Validate age in days is non-negative (if provided).

    Args:
        days: Age in days to validate (can be None)

    Raises:
        ValueError: If days is provided but is negative
    """
    if days is not None:
        if days < 0:
            raise ValueError(f"age_days cannot be negative, got {days}")


def validate_search_result(
    id_value: str,
    similarity: float,
    distance: float,
    original_similarity: Optional[float] = None,
    decay_factor: Optional[float] = None,
    age_days: Optional[float] = None
) -> None:
    """
    Validate all fields of a memory search result.

    Convenience function that validates all fields at once.

    Args:
        id_value: Memory identifier
        similarity: Similarity score
        distance: L2 distance
        original_similarity: Original similarity before decay
        decay_factor: Applied decay multiplier
        age_days: Age of memory in days

    Raises:
        ValueError: If any field fails validation
    """
    validate_id(id_value)
    validate_similarity(similarity, "similarity")
    validate_distance(distance)

    if original_similarity is not None:
        validate_similarity(original_similarity, "original_similarity")

    validate_decay_factor(decay_factor)
    validate_age_days(age_days)

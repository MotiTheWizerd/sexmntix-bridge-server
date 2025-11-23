"""
Validation utilities for semantic search tool arguments

Provides validation functions for search parameters and constraints.
"""

from typing import Dict, Any, Optional, Tuple


class SearchArgumentValidator:
    """Validates and sanitizes semantic search arguments"""

    # Constants for validation
    MAX_LIMIT = 50
    DEFAULT_LIMIT = 10
    DEFAULT_MIN_SIMILARITY = 0.7  # Changed from 0.0 for better accuracy
    DEFAULT_HALF_LIFE_DAYS = 30.0
    DEFAULT_ENABLE_TEMPORAL_DECAY = False

    @staticmethod
    def validate_similarity_range(min_similarity: float) -> Tuple[bool, Optional[str]]:
        """Validate that similarity score is within valid range

        Args:
            min_similarity: Minimum similarity threshold to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not 0.0 <= min_similarity <= 1.0:
            return False, "min_similarity must be between 0.0 and 1.0"
        return True, None

    @staticmethod
    def validate_half_life_days(half_life_days: float) -> Tuple[bool, Optional[str]]:
        """Validate that half-life days is positive

        Args:
            half_life_days: Half-life value to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if half_life_days <= 0:
            return False, "half_life_days must be greater than 0"
        return True, None

    @staticmethod
    def validate_limit(limit: int) -> int:
        """Validate and cap the result limit

        Args:
            limit: Requested result limit

        Returns:
            Validated and capped limit value
        """
        return min(int(limit), SearchArgumentValidator.MAX_LIMIT)

    @classmethod
    def extract_and_validate(
        cls,
        arguments: Dict[str, Any],
        context_user_id: str,
        context_project_id: Optional[str]
    ) -> Dict[str, Any]:
        """Extract and validate all search arguments

        Args:
            arguments: Raw arguments from tool invocation
            context_user_id: Default user ID from context (unused, kept for backward compatibility)
            context_project_id: Default project ID from context (unused, kept for backward compatibility)

        Returns:
            Dictionary of validated arguments

        Raises:
            ValueError: If validation fails
        """
        # Extract query (required)
        query = arguments.get("query")
        if not query:
            raise ValueError("query parameter is required")

        # Extract and validate limit
        limit = cls.validate_limit(arguments.get("limit", cls.DEFAULT_LIMIT))

        # Extract and validate min_similarity
        min_similarity = float(arguments.get("min_similarity", cls.DEFAULT_MIN_SIMILARITY))
        is_valid, error = cls.validate_similarity_range(min_similarity)
        if not is_valid:
            raise ValueError(error)

        # Get user_id and project_id from context (set from environment variables)
        user_id = context_user_id
        project_id = context_project_id

        # Extract temporal decay settings
        enable_temporal_decay = bool(arguments.get("enable_temporal_decay", cls.DEFAULT_ENABLE_TEMPORAL_DECAY))
        half_life_days = float(arguments.get("half_life_days", cls.DEFAULT_HALF_LIFE_DAYS))

        # Validate half_life_days
        is_valid, error = cls.validate_half_life_days(half_life_days)
        if not is_valid:
            raise ValueError(error)

        return {
            "query": query,
            "limit": limit,
            "min_similarity": min_similarity,
            "user_id": user_id,
            "project_id": project_id,
            "enable_temporal_decay": enable_temporal_decay,
            "half_life_days": half_life_days
        }

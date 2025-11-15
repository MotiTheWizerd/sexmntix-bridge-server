"""
Query Mental Notes Validators

Validates and extracts arguments for mental notes queries.
"""

from typing import Dict, Any, Optional
from .config import QueryMentalNotesConfig


class ArgumentValidator:
    """Validates arguments for mental notes queries

    Handles argument extraction, validation, and default value application.
    """

    @classmethod
    def extract_and_validate(
        cls,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract and validate all arguments

        Args:
            arguments: Raw arguments from MCP client

        Returns:
            Dictionary with validated arguments

        Raises:
            ValueError: If validation fails
        """
        # Extract optional parameters
        session_id = arguments.get("session_id")
        mental_note_id = arguments.get("mental_note_id")
        limit = arguments.get("limit", QueryMentalNotesConfig.DEFAULT_LIMIT)

        # Validate and convert mental_note_id
        validated_note_id = cls._validate_mental_note_id(mental_note_id)

        # Validate and cap limit
        validated_limit = cls._validate_limit(limit)

        # Validate session_id if provided
        validated_session_id = cls._validate_session_id(session_id)

        return {
            "session_id": validated_session_id,
            "mental_note_id": validated_note_id,
            "limit": validated_limit
        }

    @classmethod
    def _validate_mental_note_id(cls, mental_note_id: Optional[Any]) -> Optional[int]:
        """Validate and convert mental note ID

        Args:
            mental_note_id: Raw mental note ID value

        Returns:
            Validated integer ID or None

        Raises:
            ValueError: If ID is invalid
        """
        if mental_note_id is None:
            return None

        try:
            note_id = int(mental_note_id)
            if note_id <= 0:
                raise ValueError("Mental note ID must be positive")
            return note_id
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid mental_note_id: {mental_note_id}. Must be a positive integer.")

    @classmethod
    def _validate_limit(cls, limit: Any) -> int:
        """Validate and cap the limit parameter

        Args:
            limit: Raw limit value

        Returns:
            Validated and capped limit value

        Raises:
            ValueError: If limit is invalid
        """
        try:
            limit_int = int(limit)
            if limit_int <= 0:
                raise ValueError("Limit must be positive")
            # Cap at maximum limit
            return min(limit_int, QueryMentalNotesConfig.MAX_LIMIT)
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid limit: {limit}. Must be a positive integer.")

    @classmethod
    def _validate_session_id(cls, session_id: Optional[str]) -> Optional[str]:
        """Validate session ID

        Args:
            session_id: Raw session ID value

        Returns:
            Validated session ID or None

        Raises:
            ValueError: If session ID is invalid
        """
        if session_id is None:
            return None

        if not isinstance(session_id, str):
            raise ValueError(f"Invalid session_id: {session_id}. Must be a string.")

        # Allow empty string to be treated as None
        session_id = session_id.strip()
        if not session_id:
            return None

        return session_id

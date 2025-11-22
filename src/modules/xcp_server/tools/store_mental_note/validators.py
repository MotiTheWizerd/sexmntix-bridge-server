"""
Store Mental Note Validators

Validates and extracts arguments for mental note storage.
"""

import time
from typing import Dict, Any, Optional
from .config import StoreMentalNoteConfig


class ArgumentValidator:
    """Validates arguments for mental note storage

    Handles argument extraction, validation, and default value application.
    """

    @classmethod
    def extract_and_validate(
        cls,
        arguments: Dict[str, Any],
        context_user_id: str,
        context_project_id: str,
        context_session_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract and validate all arguments

        Args:
            arguments: Raw arguments from MCP client
            context_user_id: User ID from context (set from environment variables)
            context_project_id: Project ID from context (set from environment variables)
            context_session_id: Session ID from context (if available)

        Returns:
            Dictionary with validated arguments

        Raises:
            ValueError: If validation fails
        """
        # Get user_id and project_id from context (set from environment variables)
        user_id = context_user_id
        project_id = context_project_id

        # Validate required content parameter
        content = cls._validate_content(arguments.get("content"))

        # Extract optional session_id with fallback to context or generated
        session_id = cls._extract_session_id(
            arguments.get("session_id"),
            context_session_id
        )

        # Extract note_type with default
        note_type = cls._validate_note_type(
            arguments.get("note_type", StoreMentalNoteConfig.DEFAULT_NOTE_TYPE)
        )

        # Extract optional metadata
        metadata = cls._validate_metadata(arguments.get("metadata"))

        return {
            "user_id": user_id,
            "project_id": project_id,
            "content": content,
            "session_id": session_id,
            "note_type": note_type,
            "metadata": metadata
        }

    @classmethod
    def _validate_content(cls, content: Any) -> str:
        """Validate content parameter

        Args:
            content: Raw content value

        Returns:
            Validated content string

        Raises:
            ValueError: If content is invalid or empty
        """
        if content is None:
            raise ValueError("Content is required")

        if not isinstance(content, str):
            raise ValueError(f"Content must be a string, got {type(content).__name__}")

        content = content.strip()
        if not content:
            raise ValueError("Content cannot be empty")

        return content

    @classmethod
    def _extract_session_id(
        cls,
        session_id: Optional[str],
        context_session_id: Optional[str]
    ) -> str:
        """Extract session ID with fallback logic

        Args:
            session_id: Session ID from arguments
            context_session_id: Session ID from context

        Returns:
            Valid session ID (from args, context, or generated)
        """
        # Use explicit session_id if provided
        if session_id and isinstance(session_id, str):
            session_id = session_id.strip()
            if session_id:
                return session_id

        # Fallback to context session_id
        if context_session_id and isinstance(context_session_id, str):
            context_session_id = context_session_id.strip()
            if context_session_id:
                return context_session_id

        # Generate a session ID if none available
        return cls._generate_session_id()

    @classmethod
    def _generate_session_id(cls) -> str:
        """Generate a unique session ID

        Returns:
            Generated session ID with timestamp
        """
        timestamp = int(time.time())
        return f"mcp_session_{timestamp}"

    @classmethod
    def _validate_note_type(cls, note_type: Any) -> str:
        """Validate note_type parameter

        Args:
            note_type: Raw note_type value

        Returns:
            Validated note_type string

        Raises:
            ValueError: If note_type is invalid
        """
        if not isinstance(note_type, str):
            raise ValueError(f"note_type must be a string, got {type(note_type).__name__}")

        note_type = note_type.strip()
        if not note_type:
            return StoreMentalNoteConfig.DEFAULT_NOTE_TYPE

        return note_type

    @classmethod
    def _validate_metadata(cls, metadata: Any) -> Dict[str, Any]:
        """Validate metadata parameter

        Args:
            metadata: Raw metadata value

        Returns:
            Validated metadata dictionary (empty dict if None)

        Raises:
            ValueError: If metadata is invalid
        """
        if metadata is None:
            return {}

        if not isinstance(metadata, dict):
            raise ValueError(f"metadata must be an object/dict, got {type(metadata).__name__}")

        return metadata

"""
Validation utilities for embedding tool arguments

Provides validation functions for text input and tool parameters.
"""

from typing import Dict, Any


class EmbeddingArgumentValidator:
    """Validates and sanitizes embedding generation arguments"""

    # Constants for validation
    DEFAULT_RETURN_FULL_VECTOR = False

    @staticmethod
    def validate_text(text: str) -> tuple[bool, str | None]:
        """Validate that text is non-empty and meaningful

        Args:
            text: Text to validate

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not text or not text.strip():
            return False, "Text cannot be empty"
        return True, None

    @classmethod
    def extract_and_validate(
        cls,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract and validate all embedding arguments

        Args:
            arguments: Raw arguments from tool invocation

        Returns:
            Dictionary of validated arguments

        Raises:
            ValueError: If validation fails
        """
        # Extract text (required)
        text = arguments.get("text")
        if not text:
            raise ValueError("text parameter is required")

        # Validate text
        is_valid, error = cls.validate_text(text)
        if not is_valid:
            raise ValueError(error)

        # Extract return_full_vector flag
        return_full_vector = bool(arguments.get("return_full_vector", cls.DEFAULT_RETURN_FULL_VECTOR))

        return {
            "text": text,
            "return_full_vector": return_full_vector
        }

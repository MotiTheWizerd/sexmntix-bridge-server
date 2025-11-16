"""
Input validation for embedding service.

Provides validation utilities for text inputs and model parameters
in the embedding service.
"""

from typing import List, Optional
from ..exceptions import InvalidTextError
from .config import EmbeddingServiceConfig


class TextValidator:
    """Validates text inputs for embedding generation"""

    @staticmethod
    def validate_text(text: str) -> str:
        """
        Validate and clean a single text input.

        Args:
            text: Text to validate

        Returns:
            Cleaned text (stripped of whitespace)

        Raises:
            InvalidTextError: If text is empty or invalid
        """
        if not text or not text.strip():
            raise InvalidTextError("Text cannot be empty")

        return text.strip()

    @staticmethod
    def validate_texts(texts: List[str]) -> List[str]:
        """
        Validate and clean a list of text inputs.

        Args:
            texts: List of texts to validate

        Returns:
            List of cleaned texts (stripped, empty ones removed)

        Raises:
            InvalidTextError: If texts list is empty or has no valid texts
        """
        if not texts:
            raise InvalidTextError("Texts list cannot be empty")

        # Clean texts and remove empty ones
        cleaned_texts = [t.strip() for t in texts if t.strip()]

        if not cleaned_texts:
            raise InvalidTextError("No valid texts provided")

        return cleaned_texts

    @staticmethod
    def validate_model_override(
        model: Optional[str],
        default_model: str
    ) -> str:
        """
        Validate model parameter and return effective model name.

        Args:
            model: Optional model override
            default_model: Default model from provider config

        Returns:
            Effective model name to use
        """
        return model if model else default_model

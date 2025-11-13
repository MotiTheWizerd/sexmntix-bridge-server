"""
Request schemas for embedding operations.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional


class EmbeddingCreate(BaseModel):
    """Request schema for creating a single embedding."""

    text: str = Field(..., min_length=1, max_length=100000, description="Text to embed")
    provider: Optional[str] = Field(
        default="google",
        description="Embedding provider to use (google, openai, local)"
    )
    model: Optional[str] = Field(
        default=None,
        description="Specific model to use (overrides provider default)"
    )

    @field_validator("text")
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Ensure text is not just whitespace."""
        if not v.strip():
            raise ValueError("Text cannot be empty or whitespace only")
        return v.strip()


class EmbeddingBatch(BaseModel):
    """Request schema for batch embedding generation."""

    texts: List[str] = Field(..., min_length=1, max_length=100, description="List of texts to embed")
    provider: Optional[str] = Field(
        default="google",
        description="Embedding provider to use"
    )
    model: Optional[str] = Field(
        default=None,
        description="Specific model to use"
    )

    @field_validator("texts")
    @classmethod
    def validate_texts(cls, v: List[str]) -> List[str]:
        """Ensure all texts are non-empty."""
        cleaned = [text.strip() for text in v if text.strip()]
        if not cleaned:
            raise ValueError("At least one non-empty text is required")
        return cleaned

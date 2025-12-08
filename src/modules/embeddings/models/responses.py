"""
Response schemas for embedding operations.
"""

from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from datetime import datetime


class EmbeddingResponse(BaseModel):
    """Response schema for embedding generation."""

    text: str = Field(..., description="Original text that was embedded")
    embedding: List[float] = Field(..., description="Vector embedding (typically 1536 dimensions)")
    model: str = Field(..., description="Model used to generate embedding")
    provider: str = Field(..., description="Provider that generated the embedding")
    dimensions: int = Field(..., description="Number of dimensions in the embedding vector")
    cached: bool = Field(default=False, description="Whether result was retrieved from cache")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of generation")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "permission dialog UI redesign",
                "embedding": [0.0234, -0.1234, 0.5678],
                "model": "models/text-embedding-004",
                "provider": "google",
                "dimensions": 1536,
                "cached": False,
                "generated_at": "2025-11-12T10:30:00Z"
            }
        }


class EmbeddingBatchResponse(BaseModel):
    """Response schema for batch embedding generation."""

    embeddings: List[EmbeddingResponse] = Field(..., description="List of generated embeddings")
    total_count: int = Field(..., description="Total number of embeddings generated")
    cache_hits: int = Field(default=0, description="Number of embeddings served from cache")
    processing_time_seconds: float = Field(..., description="Total processing time")

    class Config:
        json_schema_extra = {
            "example": {
                "embeddings": [
                    {
                        "text": "permission dialog UI",
                        "embedding": [0.0234, -0.1234],
                        "model": "models/text-embedding-004",
                        "provider": "google",
                        "dimensions": 1536,
                        "cached": False,
                        "generated_at": "2025-11-12T10:30:00Z"
                    }
                ],
                "total_count": 1,
                "cache_hits": 0,
                "processing_time_seconds": 0.234
            }
        }


class ProviderHealthResponse(BaseModel):
    """Response schema for provider health check."""

    provider: str = Field(..., description="Provider name")
    status: Literal["healthy", "degraded", "unavailable"] = Field(..., description="Health status")
    model: str = Field(..., description="Model being used")
    latency_ms: Optional[float] = Field(None, description="Average latency in milliseconds")
    last_error: Optional[str] = Field(None, description="Last error message if any")
    checked_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp of health check")

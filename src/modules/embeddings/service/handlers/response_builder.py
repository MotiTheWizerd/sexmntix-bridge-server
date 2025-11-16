"""
Response construction for embedding service.

Builds response objects for embedding operations.
"""

from typing import List
from datetime import datetime
from ...models import (
    EmbeddingResponse,
    EmbeddingBatchResponse,
    ProviderHealthResponse
)
from ..config import EmbeddingServiceConfig


class ResponseBuilder:
    """Constructs response objects for embedding operations"""

    @staticmethod
    def build_embedding_response(
        text: str,
        embedding: List[float],
        model: str,
        provider: str,
        cached: bool
    ) -> EmbeddingResponse:
        """
        Build an embedding response.

        Args:
            text: Original text
            embedding: Embedding vector
            model: Model name
            provider: Provider name
            cached: Whether result was cached

        Returns:
            EmbeddingResponse
        """
        return EmbeddingResponse(
            text=text,
            embedding=embedding,
            model=model,
            provider=provider,
            dimensions=len(embedding),
            cached=cached,
            generated_at=datetime.utcnow()
        )

    @staticmethod
    def build_batch_response(
        embeddings: List[EmbeddingResponse],
        cache_hits: int,
        processing_time: float
    ) -> EmbeddingBatchResponse:
        """
        Build a batch embedding response.

        Args:
            embeddings: List of embedding responses
            cache_hits: Number of cache hits
            processing_time: Processing time in seconds

        Returns:
            EmbeddingBatchResponse
        """
        return EmbeddingBatchResponse(
            embeddings=embeddings,
            total_count=len(embeddings),
            cache_hits=cache_hits,
            processing_time_seconds=round(
                processing_time,
                EmbeddingServiceConfig.BATCH_TIME_PRECISION
            )
        )

    @staticmethod
    def build_health_response(
        provider: str,
        model: str,
        is_healthy: bool,
        latency_ms: float
    ) -> ProviderHealthResponse:
        """
        Build a provider health response.

        Args:
            provider: Provider name
            model: Model name
            is_healthy: Whether provider is healthy
            latency_ms: Latency in milliseconds

        Returns:
            ProviderHealthResponse
        """
        status = "healthy" if is_healthy else "unavailable"

        return ProviderHealthResponse(
            provider=provider,
            status=status,
            model=model,
            latency_ms=round(latency_ms, EmbeddingServiceConfig.DURATION_PRECISION_MS) if is_healthy else None,
            last_error=None if is_healthy else "Health check failed",
            checked_at=datetime.utcnow()
        )

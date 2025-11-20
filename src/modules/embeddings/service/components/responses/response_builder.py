"""
Response builder component.

Responsible for building response objects with consistent metadata.
"""

from typing import List
from datetime import datetime
from ....models import EmbeddingResponse, EmbeddingBatchResponse
from ...config import EmbeddingServiceConfig


class ResponseBuilder:
    """
    Builds response objects with consistent metadata.
    
    Single responsibility: Create properly formatted response objects.
    """
    
    def __init__(self, provider_name: str):
        """
        Initialize response builder.
        
        Args:
            provider_name: Name of the embedding provider
        """
        self.provider_name = provider_name
    
    def build_embedding_response(
        self,
        text: str,
        embedding: List[float],
        model: str,
        cached: bool
    ) -> EmbeddingResponse:
        """
        Build embedding response object.
        
        Args:
            text: Text that was embedded
            embedding: Generated embedding vector
            model: Model name used
            cached: Whether result was from cache
            
        Returns:
            EmbeddingResponse with all metadata
        """
        return EmbeddingResponse(
            text=text,
            embedding=embedding,
            model=model,
            provider=self.provider_name,
            dimensions=len(embedding),
            cached=cached,
            generated_at=datetime.utcnow()
        )
    
    def build_batch_response(
        self,
        embeddings: List[EmbeddingResponse],
        cache_hits: int,
        processing_time: float
    ) -> EmbeddingBatchResponse:
        """
        Build batch response object.
        
        Args:
            embeddings: List of embedding responses
            cache_hits: Number of cache hits
            processing_time: Total processing time in seconds
            
        Returns:
            EmbeddingBatchResponse with all metadata
        """
        return EmbeddingBatchResponse(
            embeddings=embeddings,
            total_count=len(embeddings),
            cache_hits=cache_hits,
            processing_time_seconds=round(processing_time, EmbeddingServiceConfig.BATCH_TIME_PRECISION)
        )

"""
FastAPI routes for embedding operations.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict

from src.modules.embeddings import (
    EmbeddingService,
    EmbeddingCreate,
    EmbeddingResponse,
    EmbeddingBatch,
    EmbeddingBatchResponse,
    ProviderHealthResponse,
    EmbeddingError,
    ProviderError,
    InvalidTextError,
)
from src.api.dependencies.embedding import get_embedding_service
from src.modules.core import Logger
from src.api.dependencies.logger import get_logger


router = APIRouter(prefix="/embeddings", tags=["embeddings"])


@router.post(
    "",
    response_model=EmbeddingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate embedding for text",
    description="Generate vector embedding for a single text using the configured provider (Google text-embedding-004 by default)"
)
async def create_embedding(
    data: EmbeddingCreate,
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    logger: Logger = Depends(get_logger)
) -> EmbeddingResponse:
    """
    Generate embedding for a single text.

    Args:
        data: Text to embed with optional provider/model override
        embedding_service: Injected embedding service
        logger: Injected logger

    Returns:
        EmbeddingResponse with vector and metadata

    Raises:
        HTTPException 400: If text is invalid
        HTTPException 503: If provider is unavailable
        HTTPException 500: For other errors
    """
    try:
        logger.info(f"Embedding request for text: {data.text[:50]}...")

        result = await embedding_service.generate_embedding(
            text=data.text,
            model=data.model
        )

        logger.info(
            f"Embedding generated successfully, dimensions: {result.dimensions}, "
            f"cached: {result.cached}"
        )

        return result

    except InvalidTextError as e:
        logger.warning(f"Invalid text error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except ProviderError as e:
        logger.error(f"Provider error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Embedding provider error: {str(e)}"
        )

    except Exception as e:
        logger.error(f"Unexpected error generating embedding: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate embedding"
        )


@router.post(
    "/batch",
    response_model=EmbeddingBatchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate embeddings for multiple texts",
    description="Efficiently generate vector embeddings for multiple texts in a single request"
)
async def create_embeddings_batch(
    data: EmbeddingBatch,
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    logger: Logger = Depends(get_logger)
) -> EmbeddingBatchResponse:
    """
    Generate embeddings for multiple texts.

    Args:
        data: List of texts to embed
        embedding_service: Injected embedding service
        logger: Injected logger

    Returns:
        EmbeddingBatchResponse with all embeddings and statistics

    Raises:
        HTTPException 400: If texts are invalid
        HTTPException 503: If provider is unavailable
        HTTPException 500: For other errors
    """
    try:
        logger.info(f"Batch embedding request for {len(data.texts)} texts")

        result = await embedding_service.generate_embeddings_batch(
            texts=data.texts,
            model=data.model
        )

        logger.info(
            f"Batch embeddings generated: {result.total_count} total, "
            f"{result.cache_hits} cache hits, "
            f"{result.processing_time_seconds}s"
        )

        return result

    except InvalidTextError as e:
        logger.warning(f"Invalid texts error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    except ProviderError as e:
        logger.error(f"Provider error in batch: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Embedding provider error: {str(e)}"
        )

    except Exception as e:
        logger.error(f"Unexpected error in batch embedding: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate batch embeddings"
        )


@router.get(
    "/health",
    response_model=ProviderHealthResponse,
    summary="Check embedding provider health",
    description="Check if the embedding provider is accessible and healthy"
)
async def health_check(
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    logger: Logger = Depends(get_logger)
) -> ProviderHealthResponse:
    """
    Check embedding provider health.

    Args:
        embedding_service: Injected embedding service
        logger: Injected logger

    Returns:
        ProviderHealthResponse with status and metrics
    """
    try:
        logger.info("Running embedding provider health check")

        result = await embedding_service.health_check()

        logger.info(f"Health check complete: status={result.status}")

        return result

    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Health check failed"
        )


@router.get(
    "/cache/stats",
    response_model=Dict,
    summary="Get cache statistics",
    description="Retrieve embedding cache performance metrics"
)
async def get_cache_stats(
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    logger: Logger = Depends(get_logger)
) -> Dict:
    """
    Get cache statistics.

    Args:
        embedding_service: Injected embedding service
        logger: Injected logger

    Returns:
        Dictionary with cache metrics
    """
    try:
        stats = embedding_service.get_cache_stats()
        logger.debug(f"Cache stats retrieved: {stats}")
        return stats

    except Exception as e:
        logger.error(f"Failed to get cache stats: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve cache statistics"
        )


@router.delete(
    "/cache",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Clear embedding cache",
    description="Clear all cached embeddings"
)
async def clear_cache(
    embedding_service: EmbeddingService = Depends(get_embedding_service),
    logger: Logger = Depends(get_logger)
) -> None:
    """
    Clear the embedding cache.

    Args:
        embedding_service: Injected embedding service
        logger: Injected logger
    """
    try:
        embedding_service.clear_cache()
        logger.info("Embedding cache cleared")

    except Exception as e:
        logger.error(f"Failed to clear cache: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cache"
        )

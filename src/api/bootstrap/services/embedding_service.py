"""
Embedding service initialization.

Handles conditional initialization of the embedding service based on API key availability.
"""

from typing import Optional
from src.modules.core import EventBus, Logger
from src.modules.embeddings import (
    EmbeddingService,
    GoogleEmbeddingProvider,
    ProviderConfig,
    EmbeddingCache,
)
from src.api.bootstrap.config import ServiceConfig


def initialize_embedding_service(
    config: ServiceConfig,
    event_bus: EventBus,
    logger: Logger
) -> Optional[EmbeddingService]:
    """Initialize embedding service if API key is available.

    Args:
        config: Service configuration containing embedding settings
        event_bus: Application event bus
        logger: Application logger

    Returns:
        EmbeddingService instance if API key is present, None otherwise
    """
    if not config.embedding.is_available:
        logger.warning("GOOGLE_API_KEY not found - embedding service disabled")
        return None

    # Create embedding provider
    embedding_config = ProviderConfig(
        provider_name=config.embedding.provider_name,
        model_name=config.embedding.model_name,
        api_key=config.embedding.api_key,
        timeout_seconds=config.embedding.timeout_seconds,
        max_retries=config.embedding.max_retries
    )
    embedding_provider = GoogleEmbeddingProvider(embedding_config)

    # Create embedding cache
    embedding_cache = EmbeddingCache(
        max_size=config.embedding.cache_size,
        ttl_hours=config.embedding.cache_ttl_hours
    )

    # Create embedding service
    embedding_service = EmbeddingService(
        event_bus=event_bus,
        logger=logger,
        provider=embedding_provider,
        cache=embedding_cache,
        cache_enabled=config.embedding.cache_enabled
    )

    logger.info("Embedding service initialized successfully")
    return embedding_service

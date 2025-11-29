"""
Embedding service - orchestrates embedding generation with caching and events.

Refactored to ultra-modular pattern with thin orchestrator coordinating
focused micro-components.
"""

import time
from typing import List, Optional
from datetime import datetime

from src.modules.core import EventBus, Logger

from ..providers import BaseEmbeddingProvider
from ..caching import EmbeddingCache
from ..models import (
    EmbeddingResponse,
    EmbeddingBatchResponse,
    ProviderHealthResponse,
)
from .config import EmbeddingServiceConfig

# Import micro-components
from .components.validation.text_validator import TextValidator
from .components.cache.cache_handler import CacheHandler
from .components.events.event_emitter import EventEmitter
from .components.responses.response_builder import ResponseBuilder
from .components.batch.batch_processor import BatchProcessor


class EmbeddingService:
    """
    Service for generating text embeddings with caching and event publishing.
    
    Orchestrator pattern: Coordinates focused micro-components.
    """

    def __init__(
        self,
        event_bus: EventBus,
        logger: Logger,
        provider: BaseEmbeddingProvider,
        cache: Optional[EmbeddingCache] = None,
        cache_enabled: bool = True
    ):
        """
        Initialize embedding service.

        Args:
            event_bus: Event bus for publishing domain events
            logger: Logger instance
            provider: Embedding provider implementation
            cache: Optional cache instance (creates default if None)
            cache_enabled: Whether to use caching
        """
        self.logger = logger
        self.provider = provider
        
        # Initialize micro-components
        self.validator = TextValidator()
        self.cache_handler = CacheHandler(
            cache=cache if cache else EmbeddingCache(),
            enabled=cache_enabled
        )
        self.event_emitter = EventEmitter(event_bus)
        self.response_builder = ResponseBuilder(provider.provider_name)
        self.batch_processor = BatchProcessor()

        # self.logger.info(
        #     f"EmbeddingService initialized with provider: {provider.provider_name}, "
        #     f"cache_enabled: {cache_enabled}"
        # )

    async def generate_embedding(
        self,
        text: str,
        model: Optional[str] = None
    ) -> EmbeddingResponse:
        """
        Generate embedding for a single text.

        Args:
            text: Text to embed
            model: Optional model override

        Returns:
            EmbeddingResponse with vector and metadata

        Raises:
            InvalidTextError: If text is invalid
            ProviderError: If embedding generation fails
        """
        # Validate input
        validated_text = self.validator.validate_single(text)
        model_name = model if model else self.provider.config.model_name

        # Check cache
        cached_embedding = self.cache_handler.get_embedding(validated_text, model_name)

        if cached_embedding:
            # Cache hit
            self.logger.debug(
                f"Cache hit for text: {validated_text[:EmbeddingServiceConfig.TEXT_PREVIEW_SHORT]}..."
            )
            
            self.event_emitter.emit_cache_hit(
                text=validated_text,
                model=model_name,
                dimensions=len(cached_embedding)
            )

            return self.response_builder.build_embedding_response(
                text=validated_text,
                embedding=cached_embedding,
                model=model_name,
                cached=True
            )

        # Cache miss - generate embedding
        self.logger.info(
            f"Generating embedding for text: {validated_text[:EmbeddingServiceConfig.TEXT_PREVIEW_SHORT]}..."
        )

        try:
            start_time = time.time()
            embedding = await self.provider.generate_embedding(validated_text)
            duration = time.time() - start_time

            # Cache the result
            self.cache_handler.store_embedding(validated_text, model_name, embedding)

            # Emit success event
            self.event_emitter.emit_generated(
                text=validated_text,
                model=model_name,
                provider=self.provider.provider_name,
                dimensions=len(embedding),
                duration=duration,
                cached=False
            )

            self.logger.info(
                f"Embedding generated successfully in {duration:.2f}s, "
                f"dimensions: {len(embedding)}"
            )

            return self.response_builder.build_embedding_response(
                text=validated_text,
                embedding=embedding,
                model=model_name,
                cached=False
            )

        except Exception as e:
            self.event_emitter.emit_error(
                text=validated_text,
                model=model_name,
                error=e
            )
            self.logger.error(f"Failed to generate embedding: {e}")
            raise

    async def generate_embeddings_batch(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> EmbeddingBatchResponse:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to embed
            model: Optional model override

        Returns:
            EmbeddingBatchResponse with all embeddings and stats
        """
        # Validate input
        cleaned_texts = self.validator.validate_batch(texts)
        model_name = model if model else self.provider.config.model_name

        self.logger.info(f"Processing batch of {len(cleaned_texts)} texts")

        start_time = time.time()

        try:
            # Delegate to batch processor
            embeddings, cache_hits = await self.batch_processor.process_batch(
                texts=cleaned_texts,
                model=model_name,
                provider=self.provider,
                cache_handler=self.cache_handler,
                response_builder=self.response_builder
            )
            
            processing_time = time.time() - start_time
            
            # Emit batch event
            newly_generated = len(cleaned_texts) - cache_hits
            self.event_emitter.emit_batch_generated(
                total_count=len(embeddings),
                cache_hits=cache_hits,
                newly_generated=newly_generated,
                processing_time=processing_time,
                model=model_name,
                provider=self.provider.provider_name
            )

            self.logger.info(
                f"Batch processing complete: {len(embeddings)} embeddings, "
                f"{cache_hits} cache hits, {processing_time:.2f}s"
            )

            return self.response_builder.build_batch_response(
                embeddings=embeddings,
                cache_hits=cache_hits,
                processing_time=processing_time
            )

        except Exception as e:
            self.logger.error(f"Batch embedding generation failed: {e}")
            raise

    async def health_check(self) -> ProviderHealthResponse:
        """Check provider health."""
        self.logger.info("Running provider health check")

        start_time = time.time()
        is_healthy = await self.provider.health_check()
        duration = time.time() - start_time
        latency_ms = duration * 1000

        response = ProviderHealthResponse(
            provider=self.provider.provider_name,
            status="healthy" if is_healthy else "unavailable",
            model=self.provider.config.model_name,
            latency_ms=round(latency_ms, EmbeddingServiceConfig.DURATION_PRECISION_MS) if is_healthy else None,
            last_error=None if is_healthy else "Health check failed",
            checked_at=datetime.utcnow()
        )

        self.event_emitter.emit_health_check(
            provider=self.provider.provider_name,
            status=response.status,
            latency_ms=response.latency_ms
        )

        return response

    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        return self.cache_handler.get_stats()

    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self.cache_handler.clear()
        self.logger.info("Embedding cache cleared")

    async def close(self):
        """Close provider connections."""
        if hasattr(self.provider, 'close'):
            await self.provider.close()
        self.logger.info("EmbeddingService closed")

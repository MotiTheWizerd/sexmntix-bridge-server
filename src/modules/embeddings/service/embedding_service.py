"""
Embedding service - orchestrates embedding generation with caching and events.

Refactored to use composition pattern with specialized components for
better maintainability, testability, and adherence to Single Responsibility Principle.
"""

from typing import List, Optional

from src.modules.core import EventBus, Logger

from ..providers import BaseEmbeddingProvider
from ..caching import EmbeddingCache
from ..models import (
    EmbeddingResponse,
    EmbeddingBatchResponse,
    ProviderHealthResponse,
)

# Import composed components
from .config import EmbeddingServiceConfig
from .validators import TextValidator
from .formatters import EmbeddingLogFormatter
from .handlers.cache_handler import CacheHandler
from .handlers.batch_processor import BatchProcessor
from .handlers.response_builder import ResponseBuilder
from .events.event_emitter import EmbeddingEventEmitter
from .utils.metrics_collector import MetricsCollector


class EmbeddingService:
    """
    Service for generating text embeddings with caching and event publishing.

    Uses composition pattern with specialized components:
    - TextValidator: Input validation
    - CacheHandler: Cache operations
    - BatchProcessor: Batch processing with cache optimization
    - ResponseBuilder: Response object construction
    - EmbeddingEventEmitter: Event publishing
    - EmbeddingLogFormatter: Log message formatting
    - MetricsCollector: Performance timing
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
        # Store core dependencies
        self.event_bus = event_bus
        self.logger = logger
        self.provider = provider

        # Initialize composed components
        self.validator = TextValidator()
        self.formatter = EmbeddingLogFormatter()
        self.cache_handler = CacheHandler(
            cache if cache else EmbeddingCache(),
            cache_enabled
        )
        self.response_builder = ResponseBuilder()
        self.event_emitter = EmbeddingEventEmitter(event_bus)
        self.metrics = MetricsCollector()

        # Initialize batch processor with dependencies
        self.batch_processor = BatchProcessor(
            self.cache_handler,
            provider,
            self.response_builder
        )

        # Log initialization
        self.logger.info(self.formatter.format_initialization(
            provider.provider_name,
            cache_enabled
        ))

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
        validated_text = self.validator.validate_text(text)
        model_name = self.validator.validate_model_override(
            model,
            self.provider.config.model_name
        )

        # Check cache
        cached_embedding = self.cache_handler.get_cached_embedding(
            validated_text,
            model_name
        )

        if cached_embedding:
            # Cache hit - build response and emit event
            self.logger.debug(self.formatter.format_cache_hit(
                validated_text[:EmbeddingServiceConfig.TEXT_PREVIEW_SHORT]
            ))

            response = self.response_builder.build_embedding_response(
                text=validated_text,
                embedding=cached_embedding,
                model=model_name,
                provider=self.provider.provider_name,
                cached=True
            )

            self.event_emitter.emit_cache_hit(
                validated_text[:EmbeddingServiceConfig.TEXT_PREVIEW_LONG],
                model_name,
                len(cached_embedding)
            )

            return response

        # Cache miss - generate embedding
        self.logger.info(self.formatter.format_generation_started(
            validated_text[:EmbeddingServiceConfig.TEXT_PREVIEW_SHORT]
        ))

        try:
            # Generate with timing
            start_time = self.metrics.start_timer()
            embedding = await self.provider.generate_embedding(validated_text)
            duration = self.metrics.calculate_duration(start_time)

            # Cache the result
            self.cache_handler.store_embedding(
                validated_text,
                model_name,
                embedding
            )

            # Build response
            response = self.response_builder.build_embedding_response(
                text=validated_text,
                embedding=embedding,
                model=model_name,
                provider=self.provider.provider_name,
                cached=False
            )

            # Emit success event
            self.event_emitter.emit_generated(
                validated_text[:EmbeddingServiceConfig.TEXT_PREVIEW_LONG],
                model_name,
                self.provider.provider_name,
                len(embedding),
                duration,
                cached=False
            )

            self.logger.info(self.formatter.format_generation_success(
                duration,
                len(embedding)
            ))

            return response

        except Exception as e:
            # Emit error event
            self.event_emitter.emit_error(
                validated_text[:EmbeddingServiceConfig.TEXT_PREVIEW_LONG],
                model_name,
                e
            )

            self.logger.error(self.formatter.format_generation_error(str(e)))
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

        Raises:
            InvalidTextError: If texts list is invalid
            ProviderError: If batch embedding generation fails
        """
        # Validate input
        cleaned_texts = self.validator.validate_texts(texts)
        model_name = self.validator.validate_model_override(
            model,
            self.provider.config.model_name
        )

        self.logger.info(self.formatter.format_batch_processing(len(cleaned_texts)))

        # Process batch with timing
        start_time = self.metrics.start_timer()

        try:
            embeddings, cache_hits = await self.batch_processor.process_batch(
                cleaned_texts,
                model_name
            )

            processing_time = self.metrics.calculate_duration(start_time)

            # Build response
            response = self.response_builder.build_batch_response(
                embeddings,
                cache_hits,
                processing_time
            )

            # Emit batch event
            newly_generated = len(cleaned_texts) - cache_hits
            self.event_emitter.emit_batch_generated(
                len(embeddings),
                cache_hits,
                newly_generated,
                processing_time,
                model_name,
                self.provider.provider_name
            )

            self.logger.info(self.formatter.format_batch_complete(
                len(embeddings),
                cache_hits,
                processing_time
            ))

            return response

        except Exception as e:
            self.logger.error(self.formatter.format_batch_error(str(e)))
            raise

    async def health_check(self) -> ProviderHealthResponse:
        """
        Check provider health.

        Returns:
            ProviderHealthResponse with status and metrics
        """
        self.logger.info(self.formatter.format_health_check())

        # Perform health check with timing
        start_time = self.metrics.start_timer()
        is_healthy = await self.provider.health_check()
        latency_ms = self.metrics.calculate_latency_ms(start_time)

        # Build response
        response = self.response_builder.build_health_response(
            self.provider.provider_name,
            self.provider.config.model_name,
            is_healthy,
            latency_ms
        )

        # Emit health check event
        self.event_emitter.emit_health_check(
            self.provider.provider_name,
            response.status,
            latency_ms if is_healthy else None
        )

        return response

    def get_cache_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache metrics
        """
        return self.cache_handler.get_stats()

    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self.cache_handler.clear()
        self.logger.info(self.formatter.format_cache_cleared())

    async def close(self):
        """Close provider connections."""
        if hasattr(self.provider, 'close'):
            await self.provider.close()
        self.logger.info(self.formatter.format_service_closed())

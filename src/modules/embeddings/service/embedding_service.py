"""
Embedding service - orchestrates embedding generation with caching and events.
"""

from typing import List, Optional
import time
from datetime import datetime

from src.services.base_service import BaseService
from src.modules.core import EventBus, Logger

from ..providers import BaseEmbeddingProvider
from ..caching import EmbeddingCache
from ..models import (
    EmbeddingResponse,
    EmbeddingBatchResponse,
    ProviderHealthResponse,
)
from ..exceptions import InvalidTextError


class EmbeddingService(BaseService):
    """
    Service for generating text embeddings with caching and event publishing.
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
        super().__init__(event_bus, logger)
        self.provider = provider
        self.cache_enabled = cache_enabled
        self.cache = cache if cache else EmbeddingCache()

        self.logger.info(
            f"EmbeddingService initialized with provider: {provider.provider_name}, "
            f"cache_enabled: {cache_enabled}"
        )

    def _register_handlers(self):
        """Register event handlers if needed."""
        # Could subscribe to events here if needed
        pass

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
        if not text or not text.strip():
            raise InvalidTextError("Text cannot be empty")

        text = text.strip()
        model_name = model or self.provider.config.model_name

        # Check cache first
        cached_embedding = None
        if self.cache_enabled:
            cached_embedding = self.cache.get(text, model_name)

        if cached_embedding:
            self.logger.debug(f"Cache hit for text: {text[:50]}...")

            response = EmbeddingResponse(
                text=text,
                embedding=cached_embedding,
                model=model_name,
                provider=self.provider.provider_name,
                dimensions=len(cached_embedding),
                cached=True,
                generated_at=datetime.utcnow()
            )

            # Publish cache hit event
            self.event_bus.publish("embedding.cache_hit", {
                "text_preview": text[:100],
                "model": model_name,
                "dimensions": len(cached_embedding)
            })

            return response

        # Cache miss - generate embedding
        self.logger.info(f"Generating embedding for text: {text[:50]}...")

        try:
            start_time = time.time()
            embedding = await self.provider.generate_embedding(text)
            duration = time.time() - start_time

            # Cache the result
            if self.cache_enabled:
                self.cache.set(text, model_name, embedding)

            response = EmbeddingResponse(
                text=text,
                embedding=embedding,
                model=model_name,
                provider=self.provider.provider_name,
                dimensions=len(embedding),
                cached=False,
                generated_at=datetime.utcnow()
            )

            # Publish success event
            self.event_bus.publish("embedding.generated", {
                "text_preview": text[:100],
                "model": model_name,
                "provider": self.provider.provider_name,
                "dimensions": len(embedding),
                "duration_seconds": duration,
                "cached": False
            })

            self.logger.info(
                f"Embedding generated successfully in {duration:.2f}s, "
                f"dimensions: {len(embedding)}"
            )

            return response

        except Exception as e:
            # Publish error event
            self.event_bus.publish("embedding.error", {
                "text_preview": text[:100],
                "model": model_name,
                "error": str(e),
                "error_type": type(e).__name__
            })

            self.logger.error(f"Failed to generate embedding: {str(e)}")
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
        if not texts:
            raise InvalidTextError("Texts list cannot be empty")

        # Clean texts
        cleaned_texts = [t.strip() for t in texts if t.strip()]
        if not cleaned_texts:
            raise InvalidTextError("No valid texts provided")

        self.logger.info(f"Processing batch of {len(cleaned_texts)} texts")

        start_time = time.time()
        embeddings_responses = []
        cache_hits = 0

        model_name = model or self.provider.config.model_name

        # Process each text (check cache, then generate if needed)
        texts_to_generate = []
        text_indices = []

        for idx, text in enumerate(cleaned_texts):
            # Check cache
            if self.cache_enabled:
                cached = self.cache.get(text, model_name)
                if cached:
                    cache_hits += 1
                    embeddings_responses.append(EmbeddingResponse(
                        text=text,
                        embedding=cached,
                        model=model_name,
                        provider=self.provider.provider_name,
                        dimensions=len(cached),
                        cached=True,
                        generated_at=datetime.utcnow()
                    ))
                    continue

            # Not in cache - need to generate
            texts_to_generate.append(text)
            text_indices.append(idx)

        # Generate embeddings for uncached texts
        if texts_to_generate:
            try:
                generated_embeddings = await self.provider.generate_embeddings_batch(
                    texts_to_generate
                )

                # Create responses and cache
                for text, embedding in zip(texts_to_generate, generated_embeddings):
                    if self.cache_enabled:
                        self.cache.set(text, model_name, embedding)

                    embeddings_responses.append(EmbeddingResponse(
                        text=text,
                        embedding=embedding,
                        model=model_name,
                        provider=self.provider.provider_name,
                        dimensions=len(embedding),
                        cached=False,
                        generated_at=datetime.utcnow()
                    ))

            except Exception as e:
                self.logger.error(f"Batch embedding generation failed: {str(e)}")
                raise

        processing_time = time.time() - start_time

        response = EmbeddingBatchResponse(
            embeddings=embeddings_responses,
            total_count=len(embeddings_responses),
            cache_hits=cache_hits,
            processing_time_seconds=round(processing_time, 3)
        )

        # Publish batch event
        self.event_bus.publish("embedding.batch_generated", {
            "total_count": len(embeddings_responses),
            "cache_hits": cache_hits,
            "newly_generated": len(texts_to_generate),
            "processing_time_seconds": processing_time,
            "model": model_name,
            "provider": self.provider.provider_name
        })

        self.logger.info(
            f"Batch processing complete: {len(embeddings_responses)} embeddings, "
            f"{cache_hits} cache hits, {processing_time:.2f}s"
        )

        return response

    async def health_check(self) -> ProviderHealthResponse:
        """
        Check provider health.

        Returns:
            ProviderHealthResponse with status and metrics
        """
        self.logger.info("Running provider health check")

        start_time = time.time()
        is_healthy = await self.provider.health_check()
        latency = (time.time() - start_time) * 1000  # Convert to ms

        status = "healthy" if is_healthy else "unavailable"

        response = ProviderHealthResponse(
            provider=self.provider.provider_name,
            status=status,
            model=self.provider.config.model_name,
            latency_ms=round(latency, 2) if is_healthy else None,
            last_error=None if is_healthy else "Health check failed",
            checked_at=datetime.utcnow()
        )

        # Publish health check event
        self.event_bus.publish("embedding.health_check", {
            "provider": self.provider.provider_name,
            "status": status,
            "latency_ms": latency if is_healthy else None
        })

        return response

    def get_cache_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache metrics
        """
        if not self.cache_enabled:
            return {"enabled": False}

        stats = self.cache.get_stats()
        stats["enabled"] = True
        return stats

    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        if self.cache_enabled:
            self.cache.clear()
            self.logger.info("Embedding cache cleared")

    async def close(self):
        """Close provider connections."""
        if hasattr(self.provider, 'close'):
            await self.provider.close()
        self.logger.info("EmbeddingService closed")

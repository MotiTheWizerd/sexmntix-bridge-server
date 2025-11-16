"""
Event publishing for embedding service.

Handles all domain event publishing for embedding operations.
"""

from typing import Optional
from src.modules.core import EventBus
from ..config import EmbeddingServiceConfig


class EmbeddingEventEmitter:
    """Publishes domain events for embedding operations"""

    def __init__(self, event_bus: EventBus):
        """
        Initialize event emitter.

        Args:
            event_bus: Event bus for publishing events
        """
        self.event_bus = event_bus

    def emit_cache_hit(
        self,
        text_preview: str,
        model: str,
        dimensions: int
    ) -> None:
        """
        Emit cache hit event.

        Args:
            text_preview: Preview of the cached text
            model: Model name
            dimensions: Embedding dimensions
        """
        self.event_bus.publish(EmbeddingServiceConfig.CACHE_HIT_EVENT, {
            "text_preview": text_preview,
            "model": model,
            "dimensions": dimensions
        })

    def emit_generated(
        self,
        text_preview: str,
        model: str,
        provider: str,
        dimensions: int,
        duration: float,
        cached: bool = False
    ) -> None:
        """
        Emit embedding generated event.

        Args:
            text_preview: Preview of the text
            model: Model name
            provider: Provider name
            dimensions: Embedding dimensions
            duration: Generation duration in seconds
            cached: Whether result was cached
        """
        self.event_bus.publish(EmbeddingServiceConfig.GENERATED_EVENT, {
            "text_preview": text_preview,
            "model": model,
            "provider": provider,
            "dimensions": dimensions,
            "duration_seconds": duration,
            "cached": cached
        })

    def emit_error(
        self,
        text_preview: str,
        model: str,
        error: Exception
    ) -> None:
        """
        Emit embedding error event.

        Args:
            text_preview: Preview of the text that failed
            model: Model name
            error: Exception that occurred
        """
        self.event_bus.publish(EmbeddingServiceConfig.ERROR_EVENT, {
            "text_preview": text_preview,
            "model": model,
            "error": str(error),
            "error_type": type(error).__name__
        })

    def emit_batch_generated(
        self,
        total_count: int,
        cache_hits: int,
        newly_generated: int,
        processing_time: float,
        model: str,
        provider: str
    ) -> None:
        """
        Emit batch generated event.

        Args:
            total_count: Total number of embeddings
            cache_hits: Number of cache hits
            newly_generated: Number of newly generated embeddings
            processing_time: Total processing time in seconds
            model: Model name
            provider: Provider name
        """
        self.event_bus.publish(EmbeddingServiceConfig.BATCH_GENERATED_EVENT, {
            "total_count": total_count,
            "cache_hits": cache_hits,
            "newly_generated": newly_generated,
            "processing_time_seconds": processing_time,
            "model": model,
            "provider": provider
        })

    def emit_health_check(
        self,
        provider: str,
        status: str,
        latency_ms: Optional[float]
    ) -> None:
        """
        Emit health check event.

        Args:
            provider: Provider name
            status: Health status (healthy/unavailable)
            latency_ms: Latency in milliseconds (None if unavailable)
        """
        self.event_bus.publish(EmbeddingServiceConfig.HEALTH_CHECK_EVENT, {
            "provider": provider,
            "status": status,
            "latency_ms": latency_ms
        })

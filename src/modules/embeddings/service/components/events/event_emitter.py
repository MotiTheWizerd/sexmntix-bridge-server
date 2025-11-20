"""
Event emitter component.

Responsible for structured event emission with consistent formatting.
"""

from typing import Optional, Dict, Any
from src.modules.core import EventBus
from ...config import EmbeddingServiceConfig


class EventEmitter:
    """
    Handles event emission with consistent formatting.
    
    Single responsibility: Emit domain events with proper structure.
    """
    
    def __init__(self, event_bus: EventBus):
        """
        Initialize event emitter.
        
        Args:
            event_bus: Event bus for publishing events
        """
        self.event_bus = event_bus
    
    def emit_cache_hit(self, text: str, model: str, dimensions: int) -> None:
        """
        Emit cache hit event.
        
        Args:
            text: Text that was looked up
            model: Model name
            dimensions: Embedding dimensions
        """
        self._emit(EmbeddingServiceConfig.CACHE_HIT_EVENT, {
            "text_preview": self._truncate_text(text, EmbeddingServiceConfig.TEXT_PREVIEW_LONG),
            "model": model,
            "dimensions": dimensions
        })
    
    def emit_generated(
        self,
        text: str,
        model: str,
        provider: str,
        dimensions: int,
        duration: float,
        cached: bool
    ) -> None:
        """
        Emit embedding generated event.
        
        Args:
            text: Text that was embedded
            model: Model name
            provider: Provider name
            dimensions: Embedding dimensions
            duration: Generation duration in seconds
            cached: Whether result was cached
        """
        self._emit(EmbeddingServiceConfig.GENERATED_EVENT, {
            "text_preview": self._truncate_text(text, EmbeddingServiceConfig.TEXT_PREVIEW_LONG),
            "model": model,
            "provider": provider,
            "dimensions": dimensions,
            "duration_seconds": round(duration, EmbeddingServiceConfig.DURATION_PRECISION_SECONDS),
            "cached": cached
        })
    
    def emit_error(self, text: str, model: str, error: Exception) -> None:
        """
        Emit error event.
        
        Args:
            text: Text that failed to embed
            model: Model name
            error: Exception that occurred
        """
        self._emit(EmbeddingServiceConfig.ERROR_EVENT, {
            "text_preview": self._truncate_text(text, EmbeddingServiceConfig.TEXT_PREVIEW_LONG),
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
            total_count: Total embeddings in batch
            cache_hits: Number of cache hits
            newly_generated: Number of newly generated embeddings
            processing_time: Total processing time in seconds
            model: Model name
            provider: Provider name
        """
        self._emit(EmbeddingServiceConfig.BATCH_GENERATED_EVENT, {
            "total_count": total_count,
            "cache_hits": cache_hits,
            "newly_generated": newly_generated,
            "processing_time_seconds": round(processing_time, EmbeddingServiceConfig.DURATION_PRECISION_SECONDS),
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
            status: Health status
            latency_ms: Latency in milliseconds (None if unhealthy)
        """
        self._emit(EmbeddingServiceConfig.HEALTH_CHECK_EVENT, {
            "provider": provider,
            "status": status,
            "latency_ms": latency_ms
        })
    
    def _emit(self, event_name: str, data: Dict[str, Any]) -> None:
        """
        Emit event to event bus.
        
        Args:
            event_name: Name of the event
            data: Event data
        """
        self.event_bus.publish(event_name, data)
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """
        Truncate text to maximum length.
        
        Args:
            text: Text to truncate
            max_length: Maximum length
            
        Returns:
            Truncated text
        """
        return text[:max_length]

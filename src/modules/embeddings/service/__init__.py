"""
Embedding service - orchestrates embedding generation with caching and events.

Refactored into modular components for better maintainability,
testability, and adherence to Single Responsibility Principle.

Architecture:
- config.py: Configuration constants and event names
- validators.py: Input validation and sanitization
- formatters.py: Logging message formatters
- handlers/: Specialized handler components
  - cache_handler.py: Cache interaction logic
  - batch_processor.py: Batch processing with cache optimization
  - response_builder.py: Response object construction
- events/event_emitter.py: Event publishing logic
- utils/metrics_collector.py: Performance timing utilities
- embedding_service.py: Main orchestrator using composition
"""

from .embedding_service import EmbeddingService

# Export composed components for testing and advanced usage
from .config import EmbeddingServiceConfig
from .validators import TextValidator
from .formatters import EmbeddingLogFormatter
from .handlers import CacheHandler, BatchProcessor, ResponseBuilder
from .events import EmbeddingEventEmitter
from .utils import MetricsCollector

__all__ = [
    # Main service (primary export)
    "EmbeddingService",

    # Composed components (for testing and advanced usage)
    "EmbeddingServiceConfig",
    "TextValidator",
    "EmbeddingLogFormatter",
    "CacheHandler",
    "BatchProcessor",
    "ResponseBuilder",
    "EmbeddingEventEmitter",
    "MetricsCollector",
]

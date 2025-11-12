"""
Embeddings Module

Provides text embedding generation capabilities using various providers (Google, OpenAI, etc.).
Supports caching, batch processing, and event-driven architecture.
"""

from .service import EmbeddingService
from .models import (
    EmbeddingCreate,
    EmbeddingResponse,
    EmbeddingBatch,
    ProviderConfig,
)
from .exceptions import (
    EmbeddingError,
    ProviderError,
    APIRateLimitError,
    InvalidTextError,
)

__all__ = [
    "EmbeddingService",
    "EmbeddingCreate",
    "EmbeddingResponse",
    "EmbeddingBatch",
    "ProviderConfig",
    "EmbeddingError",
    "ProviderError",
    "APIRateLimitError",
    "InvalidTextError",
]

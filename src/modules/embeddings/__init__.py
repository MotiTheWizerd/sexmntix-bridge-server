"""
Embeddings Module

Provides text embedding generation capabilities using various providers (Google, OpenAI, etc.).
Supports caching, batch processing, and event-driven architecture.
"""

# Service
from .service import EmbeddingService

# Models
from .models import (
    ProviderConfig,
    EmbeddingCreate,
    EmbeddingBatch,
    EmbeddingResponse,
    EmbeddingBatchResponse,
    ProviderHealthResponse,
)

# Exceptions
from .exceptions import (
    EmbeddingError,
    ProviderError,
    APIRateLimitError,
    InvalidTextError,
    ProviderConnectionError,
    ProviderTimeoutError,
)

# Caching
from .caching import EmbeddingCache

# Providers
from .providers import BaseEmbeddingProvider, GoogleEmbeddingProvider

__all__ = [
    # Service
    "EmbeddingService",
    # Models
    "ProviderConfig",
    "EmbeddingCreate",
    "EmbeddingBatch",
    "EmbeddingResponse",
    "EmbeddingBatchResponse",
    "ProviderHealthResponse",
    # Exceptions
    "EmbeddingError",
    "ProviderError",
    "APIRateLimitError",
    "InvalidTextError",
    "ProviderConnectionError",
    "ProviderTimeoutError",
    # Caching
    "EmbeddingCache",
    # Providers
    "BaseEmbeddingProvider",
    "GoogleEmbeddingProvider",
]

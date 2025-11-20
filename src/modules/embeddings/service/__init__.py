"""
Embedding service - orchestrates embedding generation with caching and events.
"""

from .embedding_service import EmbeddingService
from .config import EmbeddingServiceConfig

__all__ = [
    "EmbeddingService",
    "EmbeddingServiceConfig",
]

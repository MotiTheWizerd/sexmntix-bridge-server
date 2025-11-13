"""
Embedding Providers Module

Provides abstraction and implementations for various embedding providers.
Organized into single-responsibility components for maintainability and extensibility.
"""

from src.modules.embeddings.providers.base import BaseEmbeddingProvider
from src.modules.embeddings.providers.google import GoogleEmbeddingProvider

__all__ = ["BaseEmbeddingProvider", "GoogleEmbeddingProvider"]

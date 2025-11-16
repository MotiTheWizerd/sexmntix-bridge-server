"""
Cache operations for embedding service.

Manages caching interactions for embeddings.
"""

from typing import List, Optional
from ...caching import EmbeddingCache


class CacheHandler:
    """Handles cache operations for embeddings"""

    def __init__(self, cache: EmbeddingCache, cache_enabled: bool):
        """
        Initialize cache handler.

        Args:
            cache: Embedding cache instance
            cache_enabled: Whether caching is enabled
        """
        self.cache = cache
        self.cache_enabled = cache_enabled

    def get_cached_embedding(self, text: str, model: str) -> Optional[List[float]]:
        """
        Retrieve cached embedding if available.

        Args:
            text: Text to look up
            model: Model name

        Returns:
            Cached embedding vector or None if not found/disabled
        """
        if not self.cache_enabled:
            return None

        return self.cache.get(text, model)

    def store_embedding(self, text: str, model: str, embedding: List[float]) -> None:
        """
        Store embedding in cache.

        Args:
            text: Text key
            model: Model name
            embedding: Embedding vector to cache
        """
        if self.cache_enabled:
            self.cache.set(text, model, embedding)

    def is_cache_enabled(self) -> bool:
        """
        Check if caching is enabled.

        Returns:
            True if caching is enabled
        """
        return self.cache_enabled

    def get_stats(self) -> dict:
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

    def clear(self) -> None:
        """Clear the cache if enabled."""
        if self.cache_enabled:
            self.cache.clear()

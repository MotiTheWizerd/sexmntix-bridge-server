"""
Cache handler component.

Responsible for wrapping cache operations with enable/disable logic.
"""

from typing import List, Optional
from ....caching import EmbeddingCache


class CacheHandler:
    """
    Handles cache operations with enable/disable logic.
    
    Single responsibility: Manage embedding cache operations.
    """
    
    def __init__(self, cache: EmbeddingCache, enabled: bool = True):
        """
        Initialize cache handler.
        
        Args:
            cache: Cache instance
            enabled: Whether caching is enabled
        """
        self.cache = cache
        self.enabled = enabled
    
    def get_embedding(self, text: str, model: str) -> Optional[List[float]]:
        """
        Get embedding from cache if enabled.
        
        Args:
            text: Text to look up
            model: Model name
            
        Returns:
            Cached embedding or None if not found or disabled
        """
        if not self.enabled:
            return None
        return self.cache.get(text, model)
    
    def store_embedding(self, text: str, model: str, embedding: List[float]) -> None:
        """
        Store embedding in cache if enabled.
        
        Args:
            text: Text that was embedded
            model: Model name used
            embedding: Generated embedding vector
        """
        if self.enabled:
            self.cache.set(text, model, embedding)
    
    def get_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache stats and enabled status
        """
        if not self.enabled:
            return {"enabled": False}
        
        stats = self.cache.get_stats()
        stats["enabled"] = True
        return stats
    
    def clear(self) -> None:
        """Clear the cache if enabled."""
        if self.enabled:
            self.cache.clear()

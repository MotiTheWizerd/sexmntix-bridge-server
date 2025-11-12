"""
Caching layer for embedding results.
"""

import hashlib
from typing import List, Optional, Dict
from datetime import datetime, timedelta


class EmbeddingCache:
    """
    In-memory LRU cache for embedding results.
    Caches embeddings by text hash to avoid redundant API calls.
    """

    def __init__(self, max_size: int = 1000, ttl_hours: int = 24):
        """
        Initialize the embedding cache.

        Args:
            max_size: Maximum number of cached embeddings
            ttl_hours: Time-to-live in hours for cached entries
        """
        self.max_size = max_size
        self.ttl = timedelta(hours=ttl_hours)
        self._cache: Dict[str, dict] = {}
        self._access_times: Dict[str, datetime] = {}
        self._hit_count = 0
        self._miss_count = 0

    def _generate_key(self, text: str, model: str) -> str:
        """
        Generate cache key from text and model.

        Args:
            text: Input text
            model: Model name

        Returns:
            Cache key as hex string
        """
        content = f"{model}:{text}"
        return hashlib.sha256(content.encode()).hexdigest()

    def get(self, text: str, model: str) -> Optional[List[float]]:
        """
        Retrieve cached embedding if available and not expired.

        Args:
            text: Input text
            model: Model name

        Returns:
            Cached embedding vector or None if not found/expired
        """
        key = self._generate_key(text, model)

        if key not in self._cache:
            self._miss_count += 1
            return None

        # Check expiration
        cached_at = self._cache[key]["cached_at"]
        if datetime.utcnow() - cached_at > self.ttl:
            # Expired - remove from cache
            del self._cache[key]
            del self._access_times[key]
            self._miss_count += 1
            return None

        # Update access time for LRU
        self._access_times[key] = datetime.utcnow()
        self._hit_count += 1

        return self._cache[key]["embedding"]

    def set(self, text: str, model: str, embedding: List[float]) -> None:
        """
        Store embedding in cache.

        Args:
            text: Input text
            model: Model name
            embedding: Embedding vector to cache
        """
        key = self._generate_key(text, model)

        # Evict oldest entry if cache is full
        if len(self._cache) >= self.max_size and key not in self._cache:
            self._evict_oldest()

        now = datetime.utcnow()
        self._cache[key] = {
            "embedding": embedding,
            "cached_at": now,
            "text_preview": text[:100]  # Store preview for debugging
        }
        self._access_times[key] = now

    def _evict_oldest(self) -> None:
        """Remove the least recently accessed entry."""
        if not self._access_times:
            return

        # Find oldest access time
        oldest_key = min(self._access_times, key=self._access_times.get)

        # Remove from both caches
        del self._cache[oldest_key]
        del self._access_times[oldest_key]

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self._access_times.clear()
        self._hit_count = 0
        self._miss_count = 0

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache metrics
        """
        total_requests = self._hit_count + self._miss_count
        hit_rate = (self._hit_count / total_requests * 100) if total_requests > 0 else 0

        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
            "hit_rate_percent": round(hit_rate, 2),
            "total_requests": total_requests
        }

    def __len__(self) -> int:
        """Return number of cached entries."""
        return len(self._cache)

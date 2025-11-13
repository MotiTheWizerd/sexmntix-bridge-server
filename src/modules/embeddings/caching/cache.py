"""
In-memory LRU cache for embedding results.
Orchestrates cache storage, expiration, eviction, and metrics tracking.
"""

from typing import List, Optional
from datetime import datetime, timedelta

from .key_generator import generate_cache_key
from .cache_storage import CacheStorage
from .expiration_handler import ExpirationHandler
from .eviction_strategy import LRUEvictionStrategy
from .cache_metrics import CacheMetrics


class EmbeddingCache:
    """
    In-memory LRU cache for embedding results.
    Caches embeddings by text hash to avoid redundant API calls.

    Orchestrates specialized components:
    - CacheStorage: Low-level storage operations
    - ExpirationHandler: TTL-based expiration logic
    - LRUEvictionStrategy: Least-recently-used eviction
    - CacheMetrics: Performance tracking
    """

    def __init__(
        self,
        max_size: int = 1000,
        ttl_hours: int = 24,
        storage: Optional[CacheStorage] = None,
        metrics: Optional[CacheMetrics] = None
    ):
        """
        Initialize the embedding cache.

        Args:
            max_size: Maximum number of cached embeddings
            ttl_hours: Time-to-live in hours for cached entries
            storage: Optional CacheStorage instance (creates default if None)
            metrics: Optional CacheMetrics instance (creates default if None)
        """
        self.max_size = max_size
        self.ttl = timedelta(hours=ttl_hours)

        # Initialize components via dependency injection
        self.storage = storage if storage else CacheStorage()
        self.metrics = metrics if metrics else CacheMetrics()

    def get(self, text: str, model: str) -> Optional[List[float]]:
        """
        Retrieve cached embedding if available and not expired.

        Args:
            text: Input text
            model: Model name

        Returns:
            Cached embedding vector or None if not found/expired
        """
        key = generate_cache_key(text, model)

        # Check if key exists in storage
        if not self.storage.has_key(key):
            self.metrics.record_miss()
            return None

        # Check expiration using ExpirationHandler
        cache_dict = self.storage.get_cache_dict()
        access_times_dict = self.storage.get_access_times_dict()

        if ExpirationHandler.check_and_cleanup_if_expired(
            cache_dict,
            access_times_dict,
            key,
            self.ttl
        ):
            # Entry was expired and removed
            self.metrics.record_miss()
            return None

        # Update access time for LRU tracking
        LRUEvictionStrategy.update_access_time(access_times_dict, key)
        self.metrics.record_hit()

        # Retrieve embedding from storage
        entry = self.storage.get_entry(key)
        return entry["embedding"] if entry else None

    def set(self, text: str, model: str, embedding: List[float]) -> None:
        """
        Store embedding in cache.

        Args:
            text: Input text
            model: Model name
            embedding: Embedding vector to cache
        """
        key = generate_cache_key(text, model)

        # Check if eviction is needed using LRUEvictionStrategy
        cache_dict = self.storage.get_cache_dict()
        access_times_dict = self.storage.get_access_times_dict()

        if LRUEvictionStrategy.should_evict(
            self.storage.get_size(),
            self.max_size,
            self.storage.has_key(key)
        ):
            # Evict oldest entry
            LRUEvictionStrategy.evict_oldest(cache_dict, access_times_dict)

        # Store entry
        now = datetime.utcnow()
        entry = {
            "embedding": embedding,
            "cached_at": now,
            "text_preview": text[:100]  # Store preview for debugging
        }
        self.storage.set_entry(key, entry)
        self.storage.set_access_time(key, now)

    def clear(self) -> None:
        """Clear all cached entries."""
        self.storage.clear_all()
        self.metrics.reset()

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache metrics
        """
        return self.metrics.get_stats(
            current_size=self.storage.get_size(),
            max_size=self.max_size
        )

    def __len__(self) -> int:
        """Return number of cached entries."""
        return self.storage.get_size()

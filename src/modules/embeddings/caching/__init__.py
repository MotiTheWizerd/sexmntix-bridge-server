"""
Caching layer for embedding results.

Components:
- EmbeddingCache: Main orchestrator for caching operations
- CacheStorage: Low-level storage operations
- ExpirationHandler: TTL-based expiration logic
- LRUEvictionStrategy: Least-recently-used eviction
- CacheMetrics: Performance tracking
- generate_cache_key: Cache key generation utility
"""

from .cache import EmbeddingCache
from .key_generator import generate_cache_key
from .cache_storage import CacheStorage
from .expiration_handler import ExpirationHandler
from .eviction_strategy import LRUEvictionStrategy
from .cache_metrics import CacheMetrics

__all__ = [
    "EmbeddingCache",
    "generate_cache_key",
    "CacheStorage",
    "ExpirationHandler",
    "LRUEvictionStrategy",
    "CacheMetrics",
]

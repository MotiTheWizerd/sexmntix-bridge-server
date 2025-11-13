"""
Low-level cache storage operations.
"""

from typing import Dict, Optional, List
from datetime import datetime


class CacheStorage:
    """
    Component responsible for low-level cache storage operations.
    Manages the underlying cache dictionary and access times tracking.
    """

    def __init__(self):
        """Initialize cache storage structures."""
        self._cache: Dict[str, dict] = {}
        self._access_times: Dict[str, datetime] = {}

    def get_entry(self, key: str) -> Optional[dict]:
        """
        Retrieve a cache entry by key.

        Args:
            key: Cache key

        Returns:
            Cache entry dict or None if not found
        """
        return self._cache.get(key)

    def set_entry(self, key: str, entry: dict) -> None:
        """
        Store a cache entry.

        Args:
            key: Cache key
            entry: Entry data to store
        """
        self._cache[key] = entry

    def delete_entry(self, key: str) -> None:
        """
        Remove a cache entry.

        Args:
            key: Cache key to remove
        """
        if key in self._cache:
            del self._cache[key]
        if key in self._access_times:
            del self._access_times[key]

    def has_key(self, key: str) -> bool:
        """
        Check if key exists in cache.

        Args:
            key: Cache key to check

        Returns:
            True if key exists, False otherwise
        """
        return key in self._cache

    def get_access_time(self, key: str) -> Optional[datetime]:
        """
        Get the last access time for a key.

        Args:
            key: Cache key

        Returns:
            Last access datetime or None if not found
        """
        return self._access_times.get(key)

    def set_access_time(self, key: str, access_time: datetime) -> None:
        """
        Set the access time for a key.

        Args:
            key: Cache key
            access_time: Access timestamp
        """
        self._access_times[key] = access_time

    def get_size(self) -> int:
        """
        Get current number of entries in cache.

        Returns:
            Number of cached entries
        """
        return len(self._cache)

    def clear_all(self) -> None:
        """Clear all cache entries and access times."""
        self._cache.clear()
        self._access_times.clear()

    def get_cache_dict(self) -> Dict[str, dict]:
        """
        Get direct access to cache dictionary for bulk operations.
        Used by eviction and expiration handlers.

        Returns:
            Internal cache dictionary
        """
        return self._cache

    def get_access_times_dict(self) -> Dict[str, datetime]:
        """
        Get direct access to access times dictionary for bulk operations.
        Used by eviction and expiration handlers.

        Returns:
            Internal access times dictionary
        """
        return self._access_times

    def get_all_keys(self) -> List[str]:
        """
        Get all cache keys.

        Returns:
            List of all cache keys
        """
        return list(self._cache.keys())

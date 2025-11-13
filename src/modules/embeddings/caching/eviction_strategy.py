"""
LRU eviction strategy for cache management.
"""

from typing import Dict
from datetime import datetime


class LRUEvictionStrategy:
    """
    Component responsible for Least Recently Used (LRU) eviction logic.
    Implements cache eviction when cache reaches capacity.
    """

    @staticmethod
    def evict_oldest(
        cache: Dict[str, dict],
        access_times: Dict[str, datetime]
    ) -> None:
        """
        Remove the least recently accessed entry from cache.

        Args:
            cache: Main cache dictionary
            access_times: Access times dictionary tracking last access per key
        """
        if not access_times:
            return

        # Find key with oldest access time
        oldest_key = min(access_times, key=access_times.get)

        # Remove from both dictionaries
        if oldest_key in cache:
            del cache[oldest_key]
        if oldest_key in access_times:
            del access_times[oldest_key]

    @staticmethod
    def should_evict(
        current_size: int,
        max_size: int,
        key_exists: bool
    ) -> bool:
        """
        Determine if eviction is needed before adding new entry.

        Args:
            current_size: Current number of entries in cache
            max_size: Maximum allowed cache size
            key_exists: Whether the key being added already exists

        Returns:
            True if eviction is needed, False otherwise
        """
        # Only evict if cache is full AND we're adding a new key
        return current_size >= max_size and not key_exists

    @staticmethod
    def update_access_time(
        access_times: Dict[str, datetime],
        key: str
    ) -> None:
        """
        Update the access time for a cache entry.

        Args:
            access_times: Access times dictionary
            key: Cache key to update
        """
        access_times[key] = datetime.utcnow()

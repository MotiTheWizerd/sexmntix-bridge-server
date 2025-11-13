"""
Expiration handler for cache entries with TTL-based expiration.
"""

from typing import Dict
from datetime import datetime, timedelta


class ExpirationHandler:
    """
    Component responsible for checking cache entry expiration and cleanup.
    Handles TTL-based expiration logic.
    """

    @staticmethod
    def is_expired(cached_at: datetime, ttl: timedelta) -> bool:
        """
        Check if a cache entry has expired based on TTL.

        Args:
            cached_at: Timestamp when entry was cached
            ttl: Time-to-live duration

        Returns:
            True if entry has expired, False otherwise
        """
        return datetime.utcnow() - cached_at > ttl

    @staticmethod
    def cleanup_expired_entry(
        cache: Dict[str, dict],
        access_times: Dict[str, datetime],
        key: str
    ) -> None:
        """
        Remove an expired entry from cache storage.

        Args:
            cache: Main cache dictionary
            access_times: Access times dictionary
            key: Cache key to remove
        """
        if key in cache:
            del cache[key]
        if key in access_times:
            del access_times[key]

    @staticmethod
    def check_and_cleanup_if_expired(
        cache: Dict[str, dict],
        access_times: Dict[str, datetime],
        key: str,
        ttl: timedelta
    ) -> bool:
        """
        Check if entry is expired and cleanup if necessary.

        Args:
            cache: Main cache dictionary
            access_times: Access times dictionary
            key: Cache key to check
            ttl: Time-to-live duration

        Returns:
            True if entry was expired and removed, False if still valid
        """
        if key not in cache:
            return True  # Consider non-existent as expired

        cached_at = cache[key]["cached_at"]
        if ExpirationHandler.is_expired(cached_at, ttl):
            ExpirationHandler.cleanup_expired_entry(cache, access_times, key)
            return True

        return False

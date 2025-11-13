"""
Cache metrics tracking for performance monitoring.
"""


class CacheMetrics:
    """
    Component responsible for tracking cache performance metrics.
    Tracks hit/miss counts and calculates cache statistics.
    """

    def __init__(self):
        """Initialize metrics counters."""
        self._hit_count = 0
        self._miss_count = 0

    def record_hit(self) -> None:
        """Record a cache hit."""
        self._hit_count += 1

    def record_miss(self) -> None:
        """Record a cache miss."""
        self._miss_count += 1

    def get_hit_count(self) -> int:
        """Get total number of cache hits."""
        return self._hit_count

    def get_miss_count(self) -> int:
        """Get total number of cache misses."""
        return self._miss_count

    def get_total_requests(self) -> int:
        """Get total number of cache requests."""
        return self._hit_count + self._miss_count

    def get_hit_rate_percent(self) -> float:
        """
        Calculate cache hit rate as percentage.

        Returns:
            Hit rate percentage (0-100), or 0 if no requests
        """
        total = self.get_total_requests()
        if total == 0:
            return 0.0
        return (self._hit_count / total) * 100

    def get_stats(self, current_size: int, max_size: int) -> dict:
        """
        Get comprehensive cache statistics.

        Args:
            current_size: Current number of entries in cache
            max_size: Maximum cache size

        Returns:
            Dictionary with cache metrics
        """
        return {
            "size": current_size,
            "max_size": max_size,
            "hit_count": self._hit_count,
            "miss_count": self._miss_count,
            "hit_rate_percent": round(self.get_hit_rate_percent(), 2),
            "total_requests": self.get_total_requests()
        }

    def reset(self) -> None:
        """Reset all metrics counters."""
        self._hit_count = 0
        self._miss_count = 0

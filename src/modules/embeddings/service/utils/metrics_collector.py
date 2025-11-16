"""
Performance metrics collection utilities.

Provides timing and metrics tracking utilities for the embedding service.
"""

import time
from ..config import EmbeddingServiceConfig


class MetricsCollector:
    """Collects performance metrics and timing data"""

    @staticmethod
    def start_timer() -> float:
        """
        Start a performance timer.

        Returns:
            Start timestamp
        """
        return time.time()

    @staticmethod
    def calculate_duration(
        start_time: float,
        precision: int = EmbeddingServiceConfig.DURATION_PRECISION_SECONDS
    ) -> float:
        """
        Calculate duration in seconds since start time.

        Args:
            start_time: Start timestamp from start_timer()
            precision: Decimal places for rounding

        Returns:
            Duration in seconds
        """
        duration = time.time() - start_time
        return round(duration, precision)

    @staticmethod
    def calculate_latency_ms(
        start_time: float,
        precision: int = EmbeddingServiceConfig.DURATION_PRECISION_MS
    ) -> float:
        """
        Calculate latency in milliseconds since start time.

        Args:
            start_time: Start timestamp from start_timer()
            precision: Decimal places for rounding

        Returns:
            Latency in milliseconds
        """
        duration = time.time() - start_time
        latency_ms = duration * 1000
        return round(latency_ms, precision)

    @staticmethod
    def truncate_text(text: str, max_length: int) -> str:
        """
        Truncate text for preview purposes.

        Args:
            text: Text to truncate
            max_length: Maximum length

        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text
        return text[:max_length]

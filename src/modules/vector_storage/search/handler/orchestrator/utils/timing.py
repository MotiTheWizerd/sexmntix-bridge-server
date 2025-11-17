"""
Timing Utilities for Search Operations

Utilities for tracking and calculating search operation durations.
"""

import time


def start_timer() -> float:
    """
    Start a timer and return the start timestamp.

    Returns:
        Current timestamp in seconds
    """
    return time.time()


def calculate_duration(start_time: float) -> float:
    """
    Calculate duration from start time to now.

    Args:
        start_time: Start timestamp in seconds

    Returns:
        Duration in seconds
    """
    return time.time() - start_time


def calculate_duration_ms(start_time: float) -> float:
    """
    Calculate duration in milliseconds from start time to now.

    Args:
        start_time: Start timestamp in seconds

    Returns:
        Duration in milliseconds
    """
    return calculate_duration(start_time) * 1000


def format_duration_ms(duration_seconds: float) -> float:
    """
    Format duration from seconds to milliseconds.

    Args:
        duration_seconds: Duration in seconds

    Returns:
        Duration in milliseconds
    """
    return duration_seconds * 1000

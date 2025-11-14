"""Timestamp Converter

Converts various date formats to Unix timestamps for ChromaDB storage.
"""

from typing import Any, Optional
from datetime import datetime


def convert_to_timestamp(value: Any) -> Optional[int]:
    """
    Convert date value to Unix timestamp for ChromaDB storage.

    ChromaDB comparison operators ($gte, $lte) require numeric values.

    Args:
        value: Date value (datetime object, ISO string, or timestamp)

    Returns:
        Unix timestamp (seconds since epoch) or None if invalid

    Examples:
        datetime(2025, 10, 14) -> 1728864000
        "2025-10-14T00:00:00" -> 1728864000
        "2025-10-14" -> 1728864000
        1728864000 -> 1728864000
    """
    if value is None or value == "":
        return None

    # Already a timestamp (int or float)
    if isinstance(value, (int, float)):
        return int(value)

    # datetime object
    if isinstance(value, datetime):
        return int(value.timestamp())

    # String (ISO format)
    if isinstance(value, str):
        try:
            # Parse ISO string to datetime
            if "T" not in value:
                value = f"{value}T00:00:00"
            dt = datetime.fromisoformat(value)
            return int(dt.timestamp())
        except (ValueError, AttributeError):
            return None

    return None

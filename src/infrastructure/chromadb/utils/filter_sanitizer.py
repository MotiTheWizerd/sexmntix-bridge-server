"""Filter Sanitizer

Sanitizes and builds ChromaDB filters for metadata filtering.
"""

from typing import Any, Dict, Optional
from .timestamp_converter import convert_to_timestamp


def build_tag_filter(tag: str) -> Dict[str, Any]:
    """
    Build a filter to match any of the individual tag fields.

    Args:
        tag: Tag value to search for

    Returns:
        ChromaDB $or filter matching tag_0 through tag_4

    Example:
        Input: "chromadb"
        Output: {"$or": [{"tag_0": "chromadb"}, {"tag_1": "chromadb"}, ...]}
    """
    return {
        "$or": [
            {"tag_0": tag},
            {"tag_1": tag},
            {"tag_2": tag},
            {"tag_3": tag},
            {"tag_4": tag}
        ]
    }


def sanitize_filter(where_filter: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Sanitize ChromaDB where filter by removing empty nested objects and transforming date filters.

    ChromaDB requires each filter key to have a valid operator expression.
    Empty dicts {} are not valid and cause "Expected operator expression" errors.

    Also handles date range filtering (dates are converted to Unix timestamps):
    - 'date' field -> {'date': {'$gte': timestamp}}
    - 'end_date' field -> {'date': {'$lte': timestamp}}
    - Both combined with $and

    Args:
        where_filter: Optional metadata filter

    Returns:
        Sanitized filter or None if empty after cleaning

    Example:
        Input:  {"additionalProp1": {}, "component": "auth"}
        Output: {"component": "auth"}

        Input:  {"date": "2025-10-14", "end_date": "2025-11-13"}
        Output: {"$and": [{"date": {"$gte": 1728864000}}, {"date": {"$lte": 1731542399}}]}

        Input:  {"additionalProp1": {}}
        Output: None
    """
    if where_filter is None:
        return None

    # Remove keys with empty dict values
    cleaned_filter = {
        key: value
        for key, value in where_filter.items()
        if not (isinstance(value, dict) and len(value) == 0)
    }

    # Handle date range filtering
    date_filters = []
    other_filters = {}

    for key, value in cleaned_filter.items():
        if key == "date":
            if isinstance(value, dict):
                # Date already has operators like {"$gte": "2025-10-14", "$lte": "2025-11-13"}
                # Convert all operator values to timestamps
                converted_ops = {}
                for op, date_val in value.items():
                    timestamp = convert_to_timestamp(date_val)
                    if timestamp is not None:
                        converted_ops[op] = timestamp
                if converted_ops:
                    other_filters["date"] = converted_ops
            else:
                # Transform plain date value to $gte operator with timestamp conversion
                timestamp = convert_to_timestamp(value)
                if timestamp is not None:
                    date_filters.append({"date": {"$gte": timestamp}})
        elif key == "end_date":
            # Transform end_date to $lte operator on date field with timestamp conversion
            timestamp = convert_to_timestamp(value)
            if timestamp is not None:
                date_filters.append({"date": {"$lte": timestamp}})
        else:
            other_filters[key] = value

    # Build final filter
    if date_filters:
        if len(date_filters) == 1:
            date_filter = date_filters[0]
        else:
            date_filter = {"$and": date_filters}

        # Combine with other filters
        if other_filters:
            return {"$and": [other_filters, date_filter]}
        else:
            return date_filter

    # Return None if filter is empty after cleaning
    if len(other_filters) == 0:
        return None

    return other_filters

"""Document Builder - Transforms memory data into ChromaDB-compatible format"""

import json
from typing import Dict, Any


def extract_document_summary(memory_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract essential fields from memory data into document summary.

    Handles field extraction, tag limiting, and preserves complex objects.

    Args:
        memory_data: Complete memory log data

    Returns:
        Dictionary with essential memory fields for storage
    """
    return {
        "content": memory_data.get("content", ""),  # Main content from store_memory
        "task": memory_data.get("task", ""),
        "summary": memory_data.get("summary", ""),
        "component": memory_data.get("component", ""),
        "tags": memory_data.get("tags", [])[:10],  # Limit tags to 10
        "gotchas": memory_data.get("gotchas", []),  # Issue/solution pairs
        "lesson": memory_data.get("lesson", ""),
        "root_cause": memory_data.get("root_cause", ""),
        "solution": memory_data.get("solution", {}),  # Full solution object
    }


def build_memory_document(memory_data: Dict[str, Any]) -> str:
    """Build a complete memory document in JSON format.

    Transforms memory data into a ChromaDB-compatible document string.
    Handles complex objects by using default=str for JSON serialization.

    Args:
        memory_data: Complete memory log data

    Returns:
        JSON string representation of the document summary
    """
    document_summary = extract_document_summary(memory_data)
    return json.dumps(document_summary, default=str)


def get_content_preview(memory_data: Dict[str, Any], max_length: int = 100) -> str:
    """Get a preview of the memory content for logging.

    Args:
        memory_data: Complete memory log data
        max_length: Maximum preview length

    Returns:
        Content preview string
    """
    content = memory_data.get("content", "")
    return content[:max_length] if content else ""

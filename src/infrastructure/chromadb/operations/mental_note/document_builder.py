"""Document Builder - Transforms mental note data into ChromaDB-compatible format"""

import json
from typing import Dict, Any


def extract_document_summary(mental_note_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract essential fields from mental note data into document summary.

    Handles field extraction and preserves complex objects.

    Args:
        mental_note_data: Complete mental note data

    Returns:
        Dictionary with essential mental note fields for storage
    """
    return {
        "content": mental_note_data.get("content", ""),  # Main content
        "session_id": mental_note_data.get("sessionId", mental_note_data.get("session_id", "")),
        "note_type": mental_note_data.get("note_type", "note"),
        "metadata": mental_note_data.get("metadata", {}),
        "start_time": mental_note_data.get("startTime", mental_note_data.get("start_time", 0)),
    }


def build_mental_note_document(mental_note_data: Dict[str, Any]) -> str:
    """Build a complete mental note document in JSON format.

    Transforms mental note data into a ChromaDB-compatible document string.
    Handles complex objects by using default=str for JSON serialization.

    Args:
        mental_note_data: Complete mental note data

    Returns:
        JSON string representation of the document summary
    """
    document_summary = extract_document_summary(mental_note_data)
    return json.dumps(document_summary, default=str)


def get_content_preview(mental_note_data: Dict[str, Any], max_length: int = 100) -> str:
    """Get a preview of the mental note content for logging.

    Args:
        mental_note_data: Complete mental note data
        max_length: Maximum preview length

    Returns:
        Content preview string
    """
    content = mental_note_data.get("content", "")
    return content[:max_length] if content else ""

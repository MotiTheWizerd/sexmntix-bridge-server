"""Metadata Builder

Prepares flat metadata dictionaries for ChromaDB filtering.
"""

from typing import Any, Dict
from .timestamp_converter import convert_to_timestamp


def prepare_metadata(memory_log: Dict[str, Any], document_type: str = "memory_log") -> Dict[str, Any]:
    """
    Prepare flat metadata dictionary for ChromaDB filtering.

    ChromaDB requires flat key-value pairs (no nested objects).
    Converts lists to comma-separated strings.

    Args:
        memory_log: Memory log data dictionary
        document_type: Type of document ('memory_log', 'mental_note', etc.)

    Returns:
        Flat metadata dictionary
    """
    metadata = {
        "document_type": document_type,
        "task": memory_log.get("task", ""),
        "agent": memory_log.get("agent", ""),
        "component": memory_log.get("component", ""),
        "date": convert_to_timestamp(memory_log.get("date")),
    }

    # Add mental note specific fields if present
    if "session_id" in memory_log or "sessionId" in memory_log:
        metadata["session_id"] = memory_log.get("session_id") or memory_log.get("sessionId", "")
    if "note_type" in memory_log:
        metadata["note_type"] = memory_log.get("note_type", "note")
    if "start_time" in memory_log or "startTime" in memory_log:
        metadata["start_time"] = memory_log.get("start_time") or memory_log.get("startTime", 0)

    # Handle tags (list -> comma-separated string + individual fields)
    if "tags" in memory_log and isinstance(memory_log["tags"], list):
        tags_list = memory_log["tags"]
        metadata["tags"] = ",".join(tags_list)  # Keep combined for display

        # Store first 5 tags individually for filtering
        for i, tag in enumerate(tags_list[:5]):
            metadata[f"tag_{i}"] = tag

    # Handle temporal context
    if "temporal_context" in memory_log:
        temporal = memory_log["temporal_context"]
        if isinstance(temporal, dict):
            metadata["time_period"] = temporal.get("time_period", "")
            metadata["quarter"] = temporal.get("quarter", "")
            metadata["year"] = str(temporal.get("year", ""))

    return metadata

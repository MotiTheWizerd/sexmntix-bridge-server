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

    # Handle complexity metrics (for filtering by complexity levels)
    if "complexity" in memory_log and isinstance(memory_log["complexity"], dict):
        complexity = memory_log["complexity"]

        if "technical" in complexity and complexity["technical"]:
            metadata["complexity_technical"] = str(complexity["technical"])

        if "business" in complexity and complexity["business"]:
            metadata["complexity_business"] = str(complexity["business"])

        if "coordination" in complexity and complexity["coordination"]:
            metadata["complexity_coordination"] = str(complexity["coordination"])

    # Handle file metrics (for filtering by file modification scope)
    if "files_modified" in memory_log:
        files_modified = memory_log["files_modified"]
        if isinstance(files_modified, list):
            metadata["files_modified_count"] = len(files_modified)
        elif isinstance(files_modified, int):
            metadata["files_modified_count"] = files_modified

    if "files_touched" in memory_log and isinstance(memory_log["files_touched"], list):
        metadata["files_touched_count"] = len(memory_log["files_touched"])

    # Filter out None values (ChromaDB doesn't accept None)
    metadata = {k: v for k, v in metadata.items() if v is not None}

    return metadata


def prepare_conversation_metadata(conversation_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare flat metadata dictionary for conversation ChromaDB storage.

    ChromaDB requires flat key-value pairs (no nested objects).
    Filters out None values to prevent ChromaDB errors.

    Storage structure: user_id/conversations/{conversation_id}/
    Note: project_id is NOT stored in metadata (conversations are user-scoped only)

    Args:
        conversation_data: Conversation data dictionary

    Returns:
        Flat metadata dictionary with only non-None values
    """
    metadata = {}

    # Add core fields if they exist and are not None
    if "user_id" in conversation_data and conversation_data["user_id"] is not None:
        metadata["user_id"] = str(conversation_data["user_id"])

    # Note: project_id is NOT included - conversations are user-scoped only

    if "conversation_id" in conversation_data and conversation_data["conversation_id"]:
        metadata["conversation_id"] = str(conversation_data["conversation_id"])

    if "model" in conversation_data and conversation_data["model"]:
        metadata["model"] = str(conversation_data["model"])

    # Add message count
    if "conversation" in conversation_data:
        messages = conversation_data["conversation"]
        if isinstance(messages, list):
            metadata["message_count"] = len(messages)

    # Add timestamp if present
    if "created_at" in conversation_data and conversation_data["created_at"]:
        created_at = conversation_data["created_at"]
        # Convert to timestamp if it's a datetime string
        timestamp = convert_to_timestamp(created_at)
        if timestamp is not None:
            metadata["created_at"] = timestamp

    return metadata

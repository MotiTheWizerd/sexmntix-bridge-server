"""Document Builder - Transforms memory data into ChromaDB-compatible format"""

import json
from typing import Dict, Any


def extract_document_summary(memory_data: Dict[str, Any]) -> Dict[str, Any]:
    """Extract comprehensive fields from memory data into document summary.

    Includes all rich context fields for comprehensive retrieval.
    Stores semantic content, metadata, and full context objects.

    Args:
        memory_data: Complete memory log data

    Returns:
        Dictionary with comprehensive memory fields for storage
    """
    return {
        # Core fields
        "content": memory_data.get("content", ""),  # Main content from store_memory
        "task": memory_data.get("task", ""),
        "summary": memory_data.get("summary", ""),
        "component": memory_data.get("component", ""),
        "tags": memory_data.get("tags", [])[:10],  # Limit tags to 10

        # Semantic learning fields
        "gotchas": memory_data.get("gotchas", []),  # Issue/solution pairs
        "lesson": memory_data.get("lesson", ""),
        "root_cause": memory_data.get("root_cause", ""),
        "solution": memory_data.get("solution", {}),  # Full solution object

        # Complexity metrics
        "complexity": memory_data.get("complexity", {}),  # Technical/business/coordination

        # Outcomes
        "outcomes": memory_data.get("outcomes", {}),  # Performance/test coverage/technical debt

        # Code context
        "code_context": memory_data.get("code_context", {}),  # Patterns/API/dependencies

        # Semantic context
        "semantic_context": memory_data.get("semantic_context", {}),  # Domain concepts/patterns

        # Future planning
        "future_planning": memory_data.get("future_planning", {}),  # Next steps/extension points

        # Validation
        "validation": memory_data.get("validation", ""),

        # File context
        "files_modified": memory_data.get("files_modified", []),
        "files_touched": memory_data.get("files_touched", []),

        # Related tasks
        "related_tasks": memory_data.get("related_tasks", []),

        # Agent and date
        "agent": memory_data.get("agent", ""),
        "date": memory_data.get("date", ""),
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

"""
Store Memory Tool Data Builders

Builds raw_data structures for memory storage.
Supports both new comprehensive format and legacy format for backward compatibility.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime
from src.modules.core.temporal_context import TemporalContextCalculator


class MemoryDataBuilder:
    """Builds raw_data structures for memory storage"""

    @classmethod
    def build_raw_data(
        cls,
        task: str,
        agent: str,
        date: str,
        user_id: str,
        project_id: str,
        datetime_iso: str,
        session_id: Optional[str] = None,
        memory_log_data: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        content: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Build the complete raw_data structure with comprehensive format.

        New comprehensive structure:
        {
            "user_id": "uuid-string",
            "project_id": "default",
            "session_id": "string",
            "datetime": "2025-11-15T23:45:00",
            "memory_log": {
                "task": "task-name-kebab-case",
                "agent": "claude-sonnet-4",
                "date": "2025-01-15",
                "component": "component-name",
                "temporal_context": {...},  // Auto-calculated if not in memory_log_data
                "tags": ["searchable", "keywords"],  // Array format
                ... (all other comprehensive fields)
            }
        }

        Legacy format support (backward compatibility):
        If memory_log_data is not provided, builds simple structure with content/tags.

        Args:
            task: Task identifier (required)
            agent: Agent identifier (required)
            date: Date string in format "YYYY-MM-DD" (required)
            user_id: User identifier
            project_id: Project identifier
            datetime_iso: ISO format datetime string (system-generated)
            session_id: Optional session identifier
            memory_log_data: Optional complete memory log data dict (new format)
            tags: Optional list of tags (legacy format, kept as array)
            metadata: Optional additional metadata (legacy format)
            content: Optional content string (legacy format)

        Returns:
            Dict[str, Any]: Complete raw_data structure ready for storage
        """
        # If memory_log_data is provided, use comprehensive format
        if memory_log_data:
            # Ensure temporal_context is calculated if not present
            if "temporal_context" not in memory_log_data or memory_log_data["temporal_context"] is None:
                from datetime import datetime as dt
                try:
                    date_obj = dt.strptime(date, "%Y-%m-%d").date()
                except ValueError:
                    date_obj = dt.fromisoformat(date.replace('Z', '+00:00')).date()
                
                temporal_context_data = TemporalContextCalculator.calculate_temporal_context(date_obj)
                memory_log_data["temporal_context"] = temporal_context_data

            # Ensure tags are in array format (not tag_0, tag_1)
            if "tags" in memory_log_data and isinstance(memory_log_data["tags"], list):
                # Already in array format, keep as is
                pass
            elif tags and isinstance(tags, list):
                memory_log_data["tags"] = tags

            # Build top-level structure with session_id
            raw_data = {
                "user_id": user_id,
                "project_id": project_id,
                "session_id": session_id,
                "datetime": datetime_iso,
                "memory_log": memory_log_data
            }
        else:
            # Legacy format: build simple structure
            memory_log_data = {
                "task": task,
                "agent": agent,
                "date": date
            }

            # Add content if provided (legacy)
            if content:
                memory_log_data["content"] = content

            # Add tags as array (not tag_0, tag_1)
            if tags and isinstance(tags, list) and len(tags) > 0:
                memory_log_data["tags"] = tags

            # Merge additional metadata if provided
            if metadata and isinstance(metadata, dict):
                memory_log_data.update(metadata)

            # Calculate temporal_context for legacy format too
            from datetime import datetime as dt
            try:
                date_obj = dt.strptime(date, "%Y-%m-%d").date()
            except ValueError:
                date_obj = dt.fromisoformat(date.replace('Z', '+00:00')).date()
            
            temporal_context_data = TemporalContextCalculator.calculate_temporal_context(date_obj)
            memory_log_data["temporal_context"] = temporal_context_data

            # Build top-level structure
            raw_data = {
                "user_id": user_id,
                "project_id": project_id,
                "session_id": session_id,
                "datetime": datetime_iso,
                "memory_log": memory_log_data
            }

        return raw_data

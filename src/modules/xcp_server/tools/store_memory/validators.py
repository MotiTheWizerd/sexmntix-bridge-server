"""
Store Memory Tool Validators

Argument validation and extraction logic for the store_memory tool.
"""

from typing import Dict, Any, Tuple, Optional, List
from datetime import datetime
from src.modules.xcp_server.models.config import ToolContext
from src.modules.xcp_server.tools.store_memory.config import StoreMemoryConfig


class MemoryArgumentValidator:
    """Validates and extracts arguments for memory storage"""

    MAX_TAGS = StoreMemoryConfig.MAX_TAGS
    DEFAULT_AGENT = StoreMemoryConfig.DEFAULT_AGENT

    @staticmethod
    def validate_content(content: Any) -> Tuple[bool, Optional[str]]:
        """Validate content is not empty

        Args:
            content: Content value to validate

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not content:
            return False, "Content is required"

        if not isinstance(content, str):
            return False, "Content must be a string"

        if not content.strip():
            return False, "Content cannot be empty"

        return True, None

    @staticmethod
    def validate_task(task: Any) -> Tuple[bool, Optional[str]]:
        """Validate task is not empty

        Args:
            task: Task value to validate

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if not task:
            return False, "Task is required"

        if not isinstance(task, str):
            return False, "Task must be a string"

        if not task.strip():
            return False, "Task cannot be empty"

        return True, None

    @classmethod
    def validate_tags(cls, tags: Any) -> Tuple[bool, Optional[str]]:
        """Validate tags array (max 5 tags)

        Args:
            tags: Tags value to validate

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if tags is None:
            return True, None

        if not isinstance(tags, list):
            return False, "Tags must be an array"

        if len(tags) > cls.MAX_TAGS:
            return False, f"Maximum of {cls.MAX_TAGS} tags allowed"

        return True, None

    @staticmethod
    def validate_metadata(metadata: Any) -> Tuple[bool, Optional[str]]:
        """Validate metadata is a dictionary

        Args:
            metadata: Metadata value to validate

        Returns:
            Tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        if metadata is None:
            return True, None

        if not isinstance(metadata, dict):
            return False, "Metadata must be an object"

        return True, None

    @classmethod
    def extract_and_validate(
        cls,
        arguments: Dict[str, Any],
        context: ToolContext
    ) -> Dict[str, Any]:
        """Extract and validate all arguments

        Args:
            arguments: Raw arguments from tool call with comprehensive structure:
                {
                    "user_id": "uuid-string",
                    "project_id": "default",
                    "session_id": "string",
                    "memory_log": {
                        "task": "task-name-kebab-case",  // Required
                        "agent": "claude-sonnet-4",  // Required
                        "date": "2025-01-15",  // Required
                        "component": "...",
                        "temporal_context": {...},
                        "complexity": {...},
                        "outcomes": {...},
                        "solution": {...},
                        "gotchas": [...],
                        "code_context": {...},
                        "future_planning": {...},
                        "user_context": {...},
                        "semantic_context": {...},
                        "tags": [...],
                        ... (all other fields optional)
                    }
                }
            context: Execution context

        Returns:
            Dict[str, Any]: Validated arguments with datetime added

        Raises:
            ValueError: If validation fails
        """
        # Get user_id and project_id from context (set from environment variables)
        user_id = context.user_id
        project_id = context.project_id
        session_id = arguments.get("session_id")
        memory_log = arguments.get("memory_log")

        # Validate memory_log
        if not memory_log or not isinstance(memory_log, dict):
            raise ValueError("memory_log is required and must be an object")

        # Extract required fields from nested memory_log object
        task = memory_log.get("task")
        agent = memory_log.get("agent")
        date = memory_log.get("date")

        # Validate required fields
        if not task:
            raise ValueError("task is required in memory_log")
        is_valid, error = cls.validate_task(task)
        if not is_valid:
            raise ValueError(error)

        if not agent:
            agent = cls.DEFAULT_AGENT
        if not isinstance(agent, str):
            raise ValueError("agent must be a string")

        if not date:
            raise ValueError("date is required in memory_log (format: YYYY-MM-DD)")
        if not isinstance(date, str):
            raise ValueError("date must be a string")

        # Validate date format
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
            try:
                datetime.fromisoformat(date.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError(f"Invalid date format: {date}. Expected format: YYYY-MM-DD")

        # Extract optional fields
        tags = memory_log.get("tags", [])
        content = memory_log.get("content", "")  # Legacy support
        metadata = memory_log.get("metadata", {})  # Legacy support

        # Validate optional fields
        is_valid, error = cls.validate_tags(tags)
        if not is_valid:
            raise ValueError(error)

        if content:
            is_valid, error = cls.validate_content(content)
            if not is_valid:
                raise ValueError(error)

        is_valid, error = cls.validate_metadata(metadata)
        if not is_valid:
            raise ValueError(error)

        # Add datetime field (system-generated ISO-8601 timestamp)
        current_datetime = datetime.utcnow().isoformat()

        # Return all fields including the full memory_log structure
        return {
            "task": task,
            "agent": agent,
            "date": date,
            "content": content,  # Legacy support
            "tags": tags if tags else [],
            "metadata": metadata if metadata else {},
            "user_id": str(user_id),
            "project_id": project_id,
            "session_id": session_id,
            "datetime": current_datetime,
            "memory_log_data": memory_log  # Pass through full structure
        }

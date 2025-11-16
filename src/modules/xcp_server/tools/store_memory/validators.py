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
            arguments: Raw arguments from tool call with new structure:
                {
                    "user_id": 1,
                    "project_id": "default",
                    "memory_log": {
                        "content": "...",
                        "task": "...",
                        "agent": "...",
                        "tags": [...],
                        "metadata": {...}
                    }
                }
            context: Execution context (not used for user_id/project_id anymore)

        Returns:
            Dict[str, Any]: Validated arguments with datetime added

        Raises:
            ValueError: If validation fails
        """
        # Extract top-level required fields
        user_id = arguments.get("user_id")
        project_id = arguments.get("project_id")
        memory_log = arguments.get("memory_log")

        # Validate top-level fields
        if user_id is None:
            raise ValueError("user_id is required at top level")
        if not project_id:
            raise ValueError("project_id is required at top level")
        if not memory_log or not isinstance(memory_log, dict):
            raise ValueError("memory_log is required and must be an object")

        # Extract fields from nested memory_log object (all optional now)
        content = memory_log.get("content", "")
        task = memory_log.get("task", "")
        agent = memory_log.get("agent", cls.DEFAULT_AGENT)
        tags = memory_log.get("tags", [])
        metadata = memory_log.get("metadata", {})

        # Validate content if provided (only validate non-empty values)
        if content:
            is_valid, error = cls.validate_content(content)
            if not is_valid:
                raise ValueError(error)

        # Validate task if provided (only validate non-empty values)
        if task:
            is_valid, error = cls.validate_task(task)
            if not is_valid:
                raise ValueError(error)

        # Validate optional fields
        is_valid, error = cls.validate_tags(tags)
        if not is_valid:
            raise ValueError(error)

        is_valid, error = cls.validate_metadata(metadata)
        if not is_valid:
            raise ValueError(error)

        # Add datetime field (system-generated)
        current_datetime = datetime.utcnow().isoformat()

        return {
            "content": content,
            "task": task,
            "agent": agent,
            "tags": tags if tags else [],
            "metadata": metadata if metadata else {},
            "user_id": str(user_id),
            "project_id": project_id,
            "datetime": current_datetime
        }

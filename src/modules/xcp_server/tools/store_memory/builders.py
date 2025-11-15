"""
Store Memory Tool Data Builders

Builds raw_data structures for memory storage with tag formatting.
"""

from typing import Dict, Any, List
from datetime import datetime


class MemoryDataBuilder:
    """Builds raw_data structures for memory storage"""

    @staticmethod
    def format_tags(tags: List[str]) -> Dict[str, str]:
        """Convert tags list to tag_0, tag_1, etc. format

        This format is used for storing tags in the raw_data JSONB column,
        making them easily accessible for querying and filtering.

        Args:
            tags: List of tag strings (max 5)

        Returns:
            Dict[str, str]: Dictionary with keys tag_0, tag_1, etc.

        Example:
            >>> format_tags(["python", "async", "database"])
            {"tag_0": "python", "tag_1": "async", "tag_2": "database"}
        """
        return {
            f"tag_{i}": str(tag)
            for i, tag in enumerate(tags[:5])  # Max 5 tags
        }

    @classmethod
    def build_raw_data(
        cls,
        task: str,
        agent: str,
        content: str,
        user_id: str,
        project_id: str,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Build the complete raw_data structure

        The raw_data structure contains all memory information in a JSONB format
        that will be stored in the database and used for vector embeddings.

        Args:
            task: Task or category (e.g., 'bug_fix', 'learning')
            agent: Source agent (e.g., 'claude', 'user', 'mcp_client')
            content: Main memory content
            user_id: User identifier
            project_id: Project identifier
            tags: Optional list of tags (max 5)
            metadata: Optional additional metadata

        Returns:
            Dict[str, Any]: Complete raw_data structure ready for storage
        """
        # Build base structure
        raw_data = {
            "task": task,
            "agent": agent,
            "date": datetime.utcnow().isoformat(),
            "content": content,
            "user_id": user_id,
            "project_id": project_id
        }

        # Add formatted tags if provided
        if tags and isinstance(tags, list) and len(tags) > 0:
            tag_data = cls.format_tags(tags)
            raw_data.update(tag_data)

        # Merge additional metadata if provided
        if metadata and isinstance(metadata, dict):
            raw_data.update(metadata)

        return raw_data

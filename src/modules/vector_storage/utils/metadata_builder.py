"""
Metadata Builder

Extract and build metadata from memory log data structures.
"""

from typing import Dict, Any, Optional
from datetime import datetime


class MetadataBuilder:
    """
    Build metadata dictionaries from memory log data.

    Extracts relevant metadata fields from memory data structures
    for storage and filtering in ChromaDB.
    """

    # Standard metadata fields to extract
    METADATA_FIELDS = [
        "id",
        "user_id",
        "project_id",
        "task",
        "agent",
        "component",
        "date",
        "tags",
    ]

    @staticmethod
    def build_from_memory_data(
        memory_data: Dict[str, Any],
        memory_log_id: Optional[int] = None,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build metadata dictionary from memory log data.

        Extracts standard fields and any additional metadata.

        Args:
            memory_data: Complete memory log data
            memory_log_id: Database ID of memory log (optional)
            user_id: User identifier (optional, overrides data)
            project_id: Project identifier (optional, overrides data)

        Returns:
            Flat metadata dictionary suitable for ChromaDB
        """
        metadata = {}

        # Add user/project if provided
        if user_id:
            metadata["user_id"] = user_id
        elif "user_id" in memory_data:
            metadata["user_id"] = memory_data["user_id"]

        if project_id:
            metadata["project_id"] = project_id
        elif "project_id" in memory_data:
            metadata["project_id"] = memory_data["project_id"]

        # Add memory log ID
        if memory_log_id:
            metadata["memory_log_id"] = memory_log_id
        elif "id" in memory_data:
            metadata["memory_log_id"] = memory_data["id"]

        # Extract standard fields
        for field in MetadataBuilder.METADATA_FIELDS:
            if field in memory_data and memory_data[field] is not None:
                value = memory_data[field]
                # Convert lists to comma-separated strings (ChromaDB compatibility)
                if isinstance(value, list):
                    metadata[field] = ",".join(str(v) for v in value)
                else:
                    metadata[field] = str(value)

        # Add timestamp
        if "date" in memory_data and memory_data["date"]:
            metadata["timestamp"] = memory_data["date"]
        else:
            metadata["timestamp"] = datetime.utcnow().isoformat()

        return metadata

    @staticmethod
    def extract_tags(memory_data: Dict[str, Any]) -> list[str]:
        """
        Extract tags from memory data.

        Args:
            memory_data: Complete memory log data

        Returns:
            List of tags
        """
        if "tags" not in memory_data:
            return []

        tags = memory_data["tags"]

        # Handle different tag formats
        if isinstance(tags, list):
            return [str(tag).strip() for tag in tags if tag]
        elif isinstance(tags, str):
            return [tag.strip() for tag in tags.split(",") if tag.strip()]
        else:
            return []

    @staticmethod
    def extract_component(memory_data: Dict[str, Any]) -> Optional[str]:
        """
        Extract component from memory data.

        Args:
            memory_data: Complete memory log data

        Returns:
            Component name or None
        """
        return memory_data.get("component")

    @staticmethod
    def extract_agent(memory_data: Dict[str, Any]) -> Optional[str]:
        """
        Extract agent from memory data.

        Args:
            memory_data: Complete memory log data

        Returns:
            Agent name or None
        """
        return memory_data.get("agent")

    @staticmethod
    def extract_task(memory_data: Dict[str, Any]) -> Optional[str]:
        """
        Extract task from memory data.

        Args:
            memory_data: Complete memory log data

        Returns:
            Task name or None
        """
        return memory_data.get("task")

    @staticmethod
    def extract_timestamp(memory_data: Dict[str, Any]) -> str:
        """
        Extract and format timestamp from memory data.

        Args:
            memory_data: Complete memory log data

        Returns:
            ISO-formatted timestamp string
        """
        if "date" in memory_data and memory_data["date"]:
            timestamp = memory_data["date"]
            if isinstance(timestamp, str):
                return timestamp
            elif isinstance(timestamp, datetime):
                return timestamp.isoformat()
            else:
                return str(timestamp)

        return datetime.utcnow().isoformat()

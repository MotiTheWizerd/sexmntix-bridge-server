"""
Store Memory Tool Formatters

Formats response data and event payloads for the store_memory tool.
"""

from typing import Dict, Any
from datetime import datetime


class MemoryResultFormatter:
    """Formats memory storage results and events"""

    @staticmethod
    def format_success_response(
        memory_log,
        task: str,
        content: str,
        user_id: str,
        project_id: str
    ) -> Dict[str, Any]:
        """Format successful storage response

        Args:
            memory_log: Stored memory log dict from API response
            task: Task category
            content: Memory content
            user_id: User identifier
            project_id: Project identifier

        Returns:
            Dict[str, Any]: Formatted response data with metadata
        """
        return {
            "data": {
                "memory_id": memory_log["id"],
                "task": task,
                "content": content,
                "created_at": memory_log["created_at"],
                "message": "Memory stored successfully and will be indexed for semantic search"
            },
            "metadata": {
                "user_id": user_id,
                "project_id": project_id
            }
        }

    @staticmethod
    def create_event_data(
        memory_log,
        task: str,
        agent: str,
        raw_data: Dict[str, Any],
        user_id: str,
        project_id: str
    ) -> Dict[str, Any]:
        """Build event data for memory_log.stored event

        This event triggers the async vector storage workflow,
        which generates embeddings and stores them in ChromaDB.

        Args:
            memory_log: Stored memory log object from database
            task: Task category
            agent: Source agent
            raw_data: Complete raw_data structure
            user_id: User identifier
            project_id: Project identifier

        Returns:
            Dict[str, Any]: Event payload for memory_log.stored
        """
        return {
            "memory_log_id": memory_log.id,
            "task": task,
            "agent": agent,
            "date": memory_log.date,
            "raw_data": raw_data,
            "user_id": user_id,
            "project_id": project_id,
        }

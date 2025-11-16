"""
Store Mental Note Formatters

Formats mental note storage results for MCP responses.
"""

from typing import Dict, Any
import time


class MentalNoteFormatter:
    """Formats mental note storage responses

    Handles transformation of storage results into client-friendly JSON structures.
    """

    @staticmethod
    def create_raw_data(
        content: str,
        session_id: str,
        note_type: str,
        user_id: int,
        project_id: str,
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create raw_data structure for database storage

        Args:
            content: Note content
            session_id: Session identifier
            note_type: Note type/category
            user_id: Context user ID
            project_id: Context project ID
            metadata: Additional metadata

        Returns:
            Complete raw_data dictionary
        """
        start_time = int(time.time() * 1000)  # Milliseconds timestamp

        raw_data = {
            "sessionId": session_id,
            "startTime": start_time,
            "content": content,
            "note_type": note_type,
            "user_id": user_id,
            "project_id": project_id
        }

        # Merge additional metadata
        if metadata:
            raw_data.update(metadata)

        return raw_data

    @staticmethod
    def create_response_data(
        mental_note_id: int,
        session_id: str,
        content: str,
        note_type: str,
        start_time: int,
        created_at: str,
        user_id: int,
        project_id: str
    ) -> Dict[str, Any]:
        """Create complete response data structure

        Args:
            mental_note_id: Database ID of stored note
            session_id: Session identifier
            content: Note content
            note_type: Note type/category
            start_time: Timestamp when note was created
            created_at: ISO format creation timestamp
            user_id: Context user ID
            project_id: Context project ID

        Returns:
            Complete response data dictionary
        """
        return {
            "mental_note_id": mental_note_id,
            "session_id": session_id,
            "content": content,
            "note_type": note_type,
            "start_time": start_time,
            "created_at": created_at,
            "message": "Mental note stored successfully. Vector indexing scheduled as background task.",
            "metadata": {
                "user_id": user_id,
                "project_id": project_id,
                "vector_storage": "scheduled"
            }
        }

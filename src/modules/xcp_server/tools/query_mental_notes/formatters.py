"""
Query Mental Notes Formatters

Formats mental note query results for MCP responses.
"""

from typing import Dict, Any, List, Optional


class MentalNoteFormatter:
    """Formats mental notes into structured responses

    Handles transformation of database models into client-friendly JSON structures.
    """

    @staticmethod
    def format_mental_note(note: Any) -> Dict[str, Any]:
        """Format a single mental note

        Args:
            note: Mental note database model

        Returns:
            Formatted note dictionary
        """
        return {
            "id": note.id,
            "session_id": note.session_id,
            "content": note.content,
            "note_type": note.note_type,
            "meta_data": note.meta_data,
            "created_at": note.created_at.isoformat()
        }

    @classmethod
    def format_mental_notes(cls, notes: List[Any]) -> List[Dict[str, Any]]:
        """Format multiple mental notes

        Args:
            notes: List of mental note database models

        Returns:
            List of formatted note dictionaries
        """
        return [cls.format_mental_note(note) for note in notes]

    @classmethod
    def create_response_data(
        cls,
        notes: List[Any],
        session_id: Optional[str],
        mental_note_id: Optional[int],
        limit: int,
        user_id: int,
        project_id: str
    ) -> Dict[str, Any]:
        """Create complete response data structure

        Args:
            notes: List of mental note database models
            session_id: Filter session ID (if applied)
            mental_note_id: Filter note ID (if applied)
            limit: Limit value used
            user_id: Context user ID
            project_id: Context project ID

        Returns:
            Complete response data dictionary
        """
        formatted_notes = cls.format_mental_notes(notes)

        return {
            "count": len(formatted_notes),
            "mental_notes": formatted_notes,
            "filters_applied": {
                "session_id": session_id,
                "mental_note_id": mental_note_id,
                "limit": limit
            },
            "metadata": {
                "user_id": user_id,
                "project_id": project_id
            }
        }

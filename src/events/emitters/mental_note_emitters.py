"""
Mental note event emitters
"""
from typing import Dict, Any
from .base import BaseEmitter
from ..schemas import EventType, SocketEvent, MentalNoteEvent


class MentalNoteEmitter(BaseEmitter):
    """Emitter for mental note events"""

    async def emit_mental_note_created(self, mental_note: Dict[str, Any], room: str = "mental_notes"):
        """
        Emit mental note created event

        Args:
            mental_note: Dictionary containing mental note data
            room: Socket.IO room to emit to (default: "mental_notes")
        """
        event_data = MentalNoteEvent(
            id=mental_note['id'],
            user_id=mental_note['user_id'],
            title=mental_note['title'],
            content=mental_note.get('content'),
            created_at=mental_note['created_at']
        )

        event = SocketEvent(
            event_type=EventType.MENTAL_NOTE_CREATED,
            data=event_data.model_dump(),
            room=room
        )

        await self._emit_event(event)

    async def emit_mental_note_updated(self, mental_note: Dict[str, Any], room: str = "mental_notes"):
        """
        Emit mental note updated event

        Args:
            mental_note: Dictionary containing mental note data
            room: Socket.IO room to emit to (default: "mental_notes")
        """
        event_data = MentalNoteEvent(
            id=mental_note['id'],
            user_id=mental_note['user_id'],
            title=mental_note['title'],
            content=mental_note.get('content'),
            created_at=mental_note['created_at'],
            updated_at=mental_note.get('updated_at')
        )

        event = SocketEvent(
            event_type=EventType.MENTAL_NOTE_UPDATED,
            data=event_data.model_dump(),
            room=room
        )

        await self._emit_event(event)

    async def emit_mental_note_deleted(self, mental_note_id: int, room: str = "mental_notes"):
        """
        Emit mental note deleted event

        Args:
            mental_note_id: ID of the deleted mental note
            room: Socket.IO room to emit to (default: "mental_notes")
        """
        event = SocketEvent(
            event_type=EventType.MENTAL_NOTE_DELETED,
            data={'id': mental_note_id},
            room=room
        )

        await self._emit_event(event)

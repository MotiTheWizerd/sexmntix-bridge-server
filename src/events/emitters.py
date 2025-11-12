"""
Event emitters - Helper functions to emit events from business logic
"""
from typing import Dict, Any
from datetime import datetime
from .schemas import (
    EventType,
    SocketEvent,
    MemoryLogEvent,
    MentalNoteEvent,
    UserStatusEvent
)


class EventEmitter:
    """Helper class to emit structured events"""
    
    def __init__(self, socket_service):
        self.socket_service = socket_service
    
    async def emit_memory_log_created(self, memory_log: Dict[str, Any], room: str = "memory_logs"):
        """Emit memory log created event"""
        event_data = MemoryLogEvent(
            id=memory_log['id'],
            user_id=memory_log['user_id'],
            content=memory_log['content'],
            created_at=memory_log['created_at']
        )
        
        event = SocketEvent(
            event_type=EventType.MEMORY_LOG_CREATED,
            data=event_data.model_dump(),
            room=room
        )
        
        await self.socket_service.emit_event(event)
    
    async def emit_memory_log_updated(self, memory_log: Dict[str, Any], room: str = "memory_logs"):
        """Emit memory log updated event"""
        event_data = MemoryLogEvent(
            id=memory_log['id'],
            user_id=memory_log['user_id'],
            content=memory_log['content'],
            created_at=memory_log['created_at'],
            updated_at=memory_log.get('updated_at')
        )
        
        event = SocketEvent(
            event_type=EventType.MEMORY_LOG_UPDATED,
            data=event_data.model_dump(),
            room=room
        )
        
        await self.socket_service.emit_event(event)
    
    async def emit_memory_log_deleted(self, memory_log_id: int, room: str = "memory_logs"):
        """Emit memory log deleted event"""
        event = SocketEvent(
            event_type=EventType.MEMORY_LOG_DELETED,
            data={'id': memory_log_id},
            room=room
        )
        
        await self.socket_service.emit_event(event)
    
    async def emit_mental_note_created(self, mental_note: Dict[str, Any], room: str = "mental_notes"):
        """Emit mental note created event"""
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
        
        await self.socket_service.emit_event(event)
    
    async def emit_mental_note_updated(self, mental_note: Dict[str, Any], room: str = "mental_notes"):
        """Emit mental note updated event"""
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
        
        await self.socket_service.emit_event(event)
    
    async def emit_mental_note_deleted(self, mental_note_id: int, room: str = "mental_notes"):
        """Emit mental note deleted event"""
        event = SocketEvent(
            event_type=EventType.MENTAL_NOTE_DELETED,
            data={'id': mental_note_id},
            room=room
        )
        
        await self.socket_service.emit_event(event)
    
    async def emit_user_status_changed(self, user_id: int, status: str, sid: str = None):
        """Emit user status changed event"""
        event_data = UserStatusEvent(
            user_id=user_id,
            status=status,
            timestamp=datetime.utcnow()
        )
        
        event = SocketEvent(
            event_type=EventType.USER_STATUS_CHANGED,
            data=event_data.model_dump(),
            sid=sid
        )
        
        await self.socket_service.emit_event(event)

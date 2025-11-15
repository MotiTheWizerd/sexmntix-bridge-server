"""
Memory log event emitters
"""
from typing import Dict, Any
from .base import BaseEmitter
from ..schemas import EventType, SocketEvent, MemoryLogEvent


class MemoryLogEmitter(BaseEmitter):
    """Emitter for memory log events"""

    async def emit_memory_log_created(self, memory_log: Dict[str, Any], room: str = "memory_logs"):
        """
        Emit memory log created event

        Args:
            memory_log: Dictionary containing memory log data
            room: Socket.IO room to emit to (default: "memory_logs")
        """
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

        await self._emit_event(event)

    async def emit_memory_log_updated(self, memory_log: Dict[str, Any], room: str = "memory_logs"):
        """
        Emit memory log updated event

        Args:
            memory_log: Dictionary containing memory log data
            room: Socket.IO room to emit to (default: "memory_logs")
        """
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

        await self._emit_event(event)

    async def emit_memory_log_deleted(self, memory_log_id: int, room: str = "memory_logs"):
        """
        Emit memory log deleted event

        Args:
            memory_log_id: ID of the deleted memory log
            room: Socket.IO room to emit to (default: "memory_logs")
        """
        event = SocketEvent(
            event_type=EventType.MEMORY_LOG_DELETED,
            data={'id': memory_log_id},
            room=room
        )

        await self._emit_event(event)

"""
User status event emitters
"""
from datetime import datetime
from .base import BaseEmitter
from ..schemas import EventType, SocketEvent, UserStatusEvent


class UserEmitter(BaseEmitter):
    """Emitter for user-related events"""

    async def emit_user_status_changed(self, user_id: int, status: str, sid: str = None):
        """
        Emit user status changed event

        Args:
            user_id: ID of the user whose status changed
            status: New status value
            sid: Optional session ID to emit to specific client
        """
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

        await self._emit_event(event)

"""
Base emitter class with common functionality
"""
from ..schemas import SocketEvent


class BaseEmitter:
    """Base class for all event emitters"""

    def __init__(self, socket_service):
        """
        Initialize the base emitter

        Args:
            socket_service: The socket service instance for emitting events
        """
        self.socket_service = socket_service

    async def _emit_event(self, event: SocketEvent):
        """
        Internal helper to emit events through socket service

        Args:
            event: The SocketEvent to emit
        """
        await self.socket_service.emit_event(event)

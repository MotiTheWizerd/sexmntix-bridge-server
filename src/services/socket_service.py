"""
Socket.IO service for real-time communication
"""
import socketio
from typing import Dict, Any
from src.modules.core import EventBus, Logger
from src.events.handlers import EventHandlerRegistry
from src.events.socket_handlers import register_all_handlers
from src.events.schemas import EventType, SocketEvent


class SocketService:
    def __init__(self, event_bus: EventBus, logger: Logger):
        self.sio = socketio.AsyncServer(
            async_mode='asgi',
            cors_allowed_origins='*',
            logger=False,
            engineio_logger=False
        )
        self.event_bus = event_bus
        self.logger = logger
        self.handler_registry = EventHandlerRegistry(logger)
        
        # Register all event handlers
        register_all_handlers(self.handler_registry, self.sio)
        
        # Setup Socket.IO lifecycle handlers
        self._setup_lifecycle_handlers()
        self._setup_dynamic_handlers()
    
    def _setup_lifecycle_handlers(self):
        """Setup connection/disconnection handlers"""
        
        @self.sio.event
        async def connect(sid, environ, auth):
            self.logger.info(f"Client connected: {sid}")
            await self.sio.emit(
                EventType.CONNECTION_ESTABLISHED.value,
                {'sid': sid},
                room=sid
            )
        
        @self.sio.event
        async def disconnect(sid):
            self.logger.info(f"Client disconnected: {sid}")
    
    def _setup_dynamic_handlers(self):
        """Setup handlers dynamically from registry"""
        for event_name, handler in self.handler_registry.get_all_handlers().items():
            @self.sio.event
            async def dynamic_handler(sid, data, event_name=event_name):
                await self.handler_registry.handle_event(event_name, sid, data, self)
            
            # Register with the actual event name
            self.sio.on(event_name, dynamic_handler)
    
    async def emit_event(self, event: SocketEvent):
        """Emit a structured event"""
        if event.sid:
            await self.emit_to_sid(event.sid, event.event_type.value, event.data)
        elif event.room:
            await self.emit_to_room(event.room, event.event_type.value, event.data)
        else:
            await self.emit_to_all(event.event_type.value, event.data)
    
    async def emit_to_room(self, room: str, event: str, data: Dict[str, Any]):
        """Emit event to specific room"""
        self.logger.debug(f"Emitting {event} to room {room}")
        await self.sio.emit(event, data, room=room)
    
    async def emit_to_all(self, event: str, data: Dict[str, Any]):
        """Emit event to all connected clients"""
        self.logger.debug(f"Emitting {event} to all clients")
        await self.sio.emit(event, data)
    
    async def emit_to_sid(self, sid: str, event: str, data: Dict[str, Any]):
        """Emit event to specific client"""
        self.logger.debug(f"Emitting {event} to client {sid}")
        await self.sio.emit(event, data, room=sid)
    
    def get_asgi_app(self):
        """Get ASGI app for mounting"""
        return socketio.ASGIApp(self.sio)

"""
Event handler registry and base handlers
"""
from typing import Callable, Dict, Any, Awaitable
from src.modules.core import Logger
from .schemas import EventType
import inspect


EventHandler = Callable[[str, Dict[str, Any], Any], Awaitable[None]]


class EventHandlerRegistry:
    """Registry for socket event handlers"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self._handlers: Dict[str, EventHandler] = {}
    
    def register(self, event_type: EventType | str):
        """Decorator to register event handlers"""
        def decorator(func: EventHandler):
            event_name = event_type.value if isinstance(event_type, EventType) else event_type
            self._handlers[event_name] = func
            self.logger.info(f"Registered handler for event: {event_name}")
            return func
        return decorator
    
    def get_handler(self, event_type: str) -> EventHandler | None:
        """Get handler for event type"""
        return self._handlers.get(event_type)
    
    def get_all_handlers(self) -> Dict[str, EventHandler]:
        """Get all registered handlers"""
        return self._handlers.copy()
    
    async def handle_event(self, event_type: str, sid: str, data: Dict[str, Any], context: Any):
        """Execute handler for event"""
        handler = self.get_handler(event_type)
        if handler:
            try:
                # Check if handler accepts context parameter
                sig = inspect.signature(handler)
                if len(sig.parameters) >= 3:
                    await handler(sid, data, context)
                else:
                    await handler(sid, data)
            except Exception as e:
                self.logger.error(f"Error handling event {event_type}: {e}")
                raise
        else:
            self.logger.warning(f"No handler registered for event: {event_type}")

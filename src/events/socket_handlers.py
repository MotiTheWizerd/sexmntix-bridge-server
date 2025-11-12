"""
Socket.IO event handlers
Organize handlers by domain/feature
"""
from typing import Dict, Any
from .schemas import EventType, PingEvent, SubscriptionEvent
from .handlers import EventHandlerRegistry


def register_connection_handlers(registry: EventHandlerRegistry, sio):
    """Register connection-related event handlers"""
    
    @registry.register(EventType.PING)
    async def handle_ping(sid: str, data: Dict[str, Any], context):
        """Handle ping event"""
        try:
            ping_data = PingEvent(**data)
            await sio.emit(EventType.PONG.value, {'timestamp': ping_data.timestamp}, room=sid)
            context.logger.debug(f"Ping/Pong with {sid}")
        except Exception as e:
            context.logger.error(f"Error in ping handler: {e}")
            await sio.emit(EventType.ERROR.value, {'message': 'Invalid ping data'}, room=sid)


def register_subscription_handlers(registry: EventHandlerRegistry, sio):
    """Register subscription-related event handlers"""
    
    @registry.register(EventType.SUBSCRIBE)
    async def handle_subscribe(sid: str, data: Dict[str, Any], context):
        """Handle subscription to event types"""
        try:
            sub_data = SubscriptionEvent(**data)
            await sio.enter_room(sid, sub_data.event_type)
            await sio.emit(
                EventType.SUBSCRIBED.value,
                {'event_type': sub_data.event_type},
                room=sid
            )
            context.logger.info(f"Client {sid} subscribed to {sub_data.event_type}")
        except Exception as e:
            context.logger.error(f"Error in subscribe handler: {e}")
            await sio.emit(EventType.ERROR.value, {'message': 'Invalid subscription data'}, room=sid)
    
    @registry.register(EventType.UNSUBSCRIBE)
    async def handle_unsubscribe(sid: str, data: Dict[str, Any], context):
        """Handle unsubscription from event types"""
        try:
            sub_data = SubscriptionEvent(**data)
            await sio.leave_room(sid, sub_data.event_type)
            await sio.emit(
                EventType.UNSUBSCRIBED.value,
                {'event_type': sub_data.event_type},
                room=sid
            )
            context.logger.info(f"Client {sid} unsubscribed from {sub_data.event_type}")
        except Exception as e:
            context.logger.error(f"Error in unsubscribe handler: {e}")
            await sio.emit(EventType.ERROR.value, {'message': 'Invalid unsubscription data'}, room=sid)


def register_memory_log_handlers(registry: EventHandlerRegistry, sio):
    """Register memory log event handlers"""
    
    # Example: Add custom handlers for memory log events
    # These would be triggered by your business logic, not directly from clients
    pass


def register_mental_note_handlers(registry: EventHandlerRegistry, sio):
    """Register mental note event handlers"""
    
    # Example: Add custom handlers for mental note events
    pass


def register_all_handlers(registry: EventHandlerRegistry, sio):
    """Register all socket event handlers"""
    register_connection_handlers(registry, sio)
    register_subscription_handlers(registry, sio)
    register_memory_log_handlers(registry, sio)
    register_mental_note_handlers(registry, sio)

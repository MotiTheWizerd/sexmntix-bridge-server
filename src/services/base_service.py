from src.modules.core import EventBus, Logger


class BaseService:
    def __init__(self, event_bus: EventBus, logger: Logger):
        self.event_bus = event_bus
        self.logger = logger
        self._register_handlers()

    def _register_handlers(self):
        """Override this method to register event handlers"""
        pass

    def subscribe(self, event_type: str, handler):
        """Helper to subscribe to events"""
        self.event_bus.subscribe(event_type, handler)
        self.logger.debug(f"Subscribed to event: {event_type}")

"""
Event Listener Registry

Auto-discovery and registration of event handlers using decorators.
"""

from typing import Callable, Dict, List, Any
from dataclasses import dataclass
import inspect
import importlib
from src.modules.core import EventBus, Logger


@dataclass
class EventHandlerInfo:
    """Information about a registered event handler"""
    event_type: str
    handler: Callable
    priority: int
    enabled: bool
    handler_class: Any  # The class instance that owns this handler
    method_name: str


class EventListenerRegistry:
    """
    Auto-discovery and registration of event handlers.

    Manages event handler discovery, registration, and subscription to the EventBus.
    """

    def __init__(self, event_bus: EventBus, logger: Logger):
        self.event_bus = event_bus
        self.logger = logger
        self._handlers: Dict[str, List[EventHandlerInfo]] = {}
        self._subscribed: bool = False

    def register_handler(
        self,
        event_type: str,
        handler: Callable,
        handler_class: Any,
        method_name: str,
        priority: int = 0,
        enabled: bool = True
    ) -> None:
        """
        Register an event handler.

        Args:
            event_type: The event type to listen for
            handler: The handler function/method
            handler_class: The class instance that owns this handler
            method_name: Name of the handler method
            priority: Handler priority (higher = called first)
            enabled: Whether handler is enabled
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []

        handler_info = EventHandlerInfo(
            event_type=event_type,
            handler=handler,
            priority=priority,
            enabled=enabled,
            handler_class=handler_class,
            method_name=method_name
        )

        self._handlers[event_type].append(handler_info)

        # Sort by priority (higher first)
        self._handlers[event_type].sort(key=lambda h: h.priority, reverse=True)

        self.logger.debug(
            f"Registered event handler: {handler_class.__class__.__name__}.{method_name} "
            f"for event '{event_type}' (priority={priority})"
        )

    def discover_handlers(self, handler_classes: List[Any]) -> None:
        """
        Discover handlers from a list of class instances.

        Args:
            handler_classes: List of class instances to scan for @event_handler decorators
        """
        self.logger.info(f"Discovering event handlers from {len(handler_classes)} classes...")

        discovered_count = 0

        for handler_class in handler_classes:
            # Get all methods of the class
            for method_name in dir(handler_class):
                if method_name.startswith('_'):
                    continue

                try:
                    method = getattr(handler_class, method_name)

                    # Check if method has event handler metadata
                    if hasattr(method, '__event_handler__'):
                        metadata = method.__event_handler__

                        self.register_handler(
                            event_type=metadata['event_type'],
                            handler=method,
                            handler_class=handler_class,
                            method_name=method_name,
                            priority=metadata.get('priority', 0),
                            enabled=metadata.get('enabled', True)
                        )

                        discovered_count += 1
                except Exception as e:
                    self.logger.warning(
                        f"Error inspecting method {method_name}: {e}"
                    )

        self.logger.info(f"Discovered {discovered_count} event handlers")

    def subscribe_all(self) -> None:
        """
        Subscribe all registered handlers to the event bus.
        """
        if self._subscribed:
            self.logger.warning("Event handlers already subscribed")
            return

        total_subscriptions = 0

        for event_type, handlers in self._handlers.items():
            enabled_handlers = [h for h in handlers if h.enabled]

            for handler_info in enabled_handlers:
                self.event_bus.subscribe(event_type, handler_info.handler)
                total_subscriptions += 1

        self._subscribed = True

        self.logger.info(
            f"Subscribed {total_subscriptions} event handlers across "
            f"{len(self._handlers)} event types"
        )

    def unsubscribe_all(self) -> None:
        """
        Unsubscribe all handlers from the event bus.

        Note: Currently EventBus doesn't support unsubscribe, but this is here for future compatibility.
        """
        self._subscribed = False
        self.logger.info("Event handlers unsubscribed")

    def get_handlers_for_event(self, event_type: str) -> List[EventHandlerInfo]:
        """
        Get all registered handlers for a specific event type.

        Args:
            event_type: The event type

        Returns:
            List of handler info objects
        """
        return self._handlers.get(event_type, [])

    def get_all_event_types(self) -> List[str]:
        """
        Get all registered event types.

        Returns:
            List of event type strings
        """
        return list(self._handlers.keys())

    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about registered handlers.

        Returns:
            Dictionary with handler statistics
        """
        total_handlers = sum(len(handlers) for handlers in self._handlers.values())
        enabled_handlers = sum(
            len([h for h in handlers if h.enabled])
            for handlers in self._handlers.values()
        )

        return {
            "total_event_types": len(self._handlers),
            "total_handlers": total_handlers,
            "enabled_handlers": enabled_handlers,
            "subscribed": self._subscribed,
            "handlers_by_event": {
                event_type: len(handlers)
                for event_type, handlers in self._handlers.items()
            }
        }

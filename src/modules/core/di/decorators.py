"""
Decorators for Dependency Injection

Provides @service and @event_handler decorators for auto-registration.
"""

from typing import Callable, Any, Type
from functools import wraps
from .container import ServiceScope


def service(scope: ServiceScope = ServiceScope.SINGLETON):
    """
    Decorator to mark a class as a service.

    Usage:
        @service(scope=ServiceScope.SINGLETON)
        class MyService:
            def __init__(self, event_bus: EventBus, logger: Logger):
                self.event_bus = event_bus
                self.logger = logger

    Args:
        scope: Service lifecycle scope (SINGLETON, TRANSIENT, SCOPED)

    Returns:
        Decorated class with service metadata
    """
    def decorator(cls: Type) -> Type:
        # Add metadata to class
        cls.__service_scope__ = scope
        cls.__is_service__ = True
        return cls

    return decorator


def event_handler(event_type: str, priority: int = 0, enabled: bool = True):
    """
    Decorator to mark a method as an event handler.

    The method will be automatically registered with the EventListenerRegistry.

    Usage:
        class MyHandlers:
            @event_handler("memory_log.stored", priority=10)
            async def handle_memory_stored(self, event_data: Dict[str, Any]):
                # Handle the event
                pass

    Args:
        event_type: The event type to listen for (e.g., "memory_log.stored")
        priority: Handler priority (higher = called first, default=0)
        enabled: Whether handler is enabled (default=True)

    Returns:
        Decorated method with event handler metadata
    """
    def decorator(func: Callable) -> Callable:
        # Add metadata to function
        func.__event_handler__ = {
            "event_type": event_type,
            "priority": priority,
            "enabled": enabled
        }

        # Preserve original function
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        # Copy metadata to wrapper
        wrapper.__event_handler__ = func.__event_handler__

        return wrapper

    return decorator


def injectable(func: Callable) -> Callable:
    """
    Decorator to mark a function for dependency injection.

    The function parameters will be automatically resolved from the DI container.

    Usage:
        @injectable
        def my_function(event_bus: EventBus, logger: Logger):
            # Dependencies auto-injected
            pass

    Args:
        func: The function to decorate

    Returns:
        Decorated function with DI metadata
    """
    func.__injectable__ = True

    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    wrapper.__injectable__ = True
    return wrapper

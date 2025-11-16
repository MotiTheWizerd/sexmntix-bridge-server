"""
Dependency Injection Module

Provides centralized service initialization and event handler registration.
"""

from .container import ServiceContainer, ServiceScope
from .event_listener_registry import EventListenerRegistry
from .decorators import service, event_handler

__all__ = [
    "ServiceContainer",
    "ServiceScope",
    "EventListenerRegistry",
    "service",
    "event_handler",
]

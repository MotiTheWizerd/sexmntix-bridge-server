from fastapi import Request
from src.modules.core import EventBus


def get_event_bus(request: Request) -> EventBus:
    return request.app.state.event_bus

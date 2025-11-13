from typing import Callable, Dict, List, Union, Awaitable
import asyncio
import inspect


class EventBus:
    """
    Event bus supporting both sync and async event handlers.

    Enables decoupled event-driven architecture where publishers
    emit events and subscribers react independently.
    """

    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, handler: Callable):
        """
        Subscribe a handler to an event type.

        Args:
            event_type: Event identifier (e.g., "memory_log.created")
            handler: Sync or async callable to handle the event
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)

    def publish(self, event_type: str, data=None):
        """
        Publish an event synchronously.

        Calls all sync handlers immediately.
        For async handlers, schedules them as background tasks.

        Args:
            event_type: Event identifier
            data: Event payload
        """
        if event_type in self._handlers:
            for handler in self._handlers[event_type]:
                if inspect.iscoroutinefunction(handler):
                    # Schedule async handler as background task
                    asyncio.create_task(handler(data))
                else:
                    # Execute sync handler immediately
                    handler(data)

    async def publish_async(self, event_type: str, data=None):
        """
        Publish an event asynchronously.

        Awaits all handlers (both sync and async) concurrently.

        Args:
            event_type: Event identifier
            data: Event payload
        """
        if event_type in self._handlers:
            tasks = []
            for handler in self._handlers[event_type]:
                if inspect.iscoroutinefunction(handler):
                    tasks.append(handler(data))
                else:
                    # Wrap sync handler in coroutine
                    tasks.append(asyncio.to_thread(handler, data))

            if tasks:
                await asyncio.gather(*tasks, return_exceptions=True)

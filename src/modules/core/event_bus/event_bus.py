from typing import Callable, Dict, List, Union, Awaitable, Set
import asyncio
import inspect
from src.modules.core.telemetry.logger import get_logger


class EventBus:
    """
    Event bus supporting both sync and async event handlers.

    Enables decoupled event-driven architecture where publishers
    emit events and subscribers react independently.
    """

    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        self._background_tasks: Set[asyncio.Task] = set()  # Keep track of tasks
        self.logger = get_logger(__name__)

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
        For async handlers, schedules them as background tasks with proper cleanup.

        Args:
            event_type: Event identifier
            data: Event payload
        """
        if event_type in self._handlers:
            self.logger.debug(f"[EVENT_BUS] Publishing event '{event_type}' to {len(self._handlers[event_type])} handler(s)")

            for handler in self._handlers[event_type]:
                if inspect.iscoroutinefunction(handler):
                    # Schedule async handler as background task with reference
                    try:
                        task = asyncio.create_task(handler(data))
                        # Keep reference and auto-cleanup when done
                        self._background_tasks.add(task)

                        # Add error logging callback
                        def log_task_exception(t: asyncio.Task):
                            self._background_tasks.discard(t)
                            if t.exception():
                                self.logger.error(
                                    f"[EVENT_BUS] Background task failed for event '{event_type}': {t.exception()}",
                                    exc_info=t.exception()
                                )
                            else:
                                self.logger.debug(f"[EVENT_BUS] Background task completed successfully for event '{event_type}'")

                        task.add_done_callback(log_task_exception)
                        self.logger.debug(f"[EVENT_BUS] Scheduled async handler for event '{event_type}'")
                    except RuntimeError as e:
                        self.logger.error(
                            f"[EVENT_BUS] Failed to create background task for event '{event_type}': {e}. "
                            f"No running event loop detected. Handler: {handler.__name__}"
                        )
                    except Exception as e:
                        self.logger.error(
                            f"[EVENT_BUS] Unexpected error scheduling handler for event '{event_type}': {e}",
                            exc_info=True
                        )
                else:
                    # Execute sync handler immediately
                    try:
                        handler(data)
                        self.logger.debug(f"[EVENT_BUS] Executed sync handler for event '{event_type}'")
                    except Exception as e:
                        self.logger.error(
                            f"[EVENT_BUS] Sync handler failed for event '{event_type}': {e}",
                            exc_info=True
                        )

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

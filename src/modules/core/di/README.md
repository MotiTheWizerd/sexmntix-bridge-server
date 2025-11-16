# Dependency Injection Module

Centralized service initialization and event handler registration for the Semantic Bridge Server.

## Overview

The DI module provides:
- **ServiceContainer**: Manages service lifecycle and dependency resolution
- **EventListenerRegistry**: Auto-discovers and registers event handlers
- **Decorators**: `@service` and `@event_handler` for declarative registration

## Quick Start

### 1. Create a Service

```python
from src.modules.core.di import service, ServiceScope
from src.modules.core import EventBus, Logger

@service(scope=ServiceScope.SINGLETON)
class MyService:
    def __init__(self, event_bus: EventBus, logger: Logger):
        self.event_bus = event_bus
        self.logger = logger

    def do_something(self):
        self.logger.info("Doing something!")
```

### 2. Create Event Handlers

```python
from src.modules.core.di import service, event_handler
from typing import Dict, Any

@service(scope=ServiceScope.SINGLETON)
class MyEventHandlers:
    def __init__(self, event_bus, logger):
        self.event_bus = event_bus
        self.logger = logger

    @event_handler("memory_log.stored", priority=10)
    async def handle_memory_stored(self, event_data: Dict[str, Any]):
        self.logger.info(f"Memory log stored: {event_data['memory_log_id']}")
        # Handle the event

    @event_handler("initialize_mcp_servers", priority=5)
    async def handle_mcp_init(self, event_data: Dict[str, Any]):
        self.logger.info(f"MCP servers initialized at {event_data['ts']}")
```

### 3. Initialize the Container

```python
from src.modules.core.di import ServiceContainer
from src.modules.core import EventBus, Logger

# Create container
container = ServiceContainer()

# Register core services
container.register_singleton(EventBus, EventBus())
container.register_singleton(Logger, Logger("app"))

# Set logger for container
container.logger = container.get(Logger)

# Register your services
container.register_class(MyService)
container.register_class(MyEventHandlers)

# Initialize all services
await container.initialize_all()

# Discover and subscribe event handlers
event_listener_registry = EventListenerRegistry(
    event_bus=container.get(EventBus),
    logger=container.get(Logger)
)

# Get all handler class instances
handler_classes = [
    container.get(MyEventHandlers),
    # Add more handler classes...
]

event_listener_registry.discover_handlers(handler_classes)
event_listener_registry.subscribe_all()

# Now all event handlers are registered!
```

### 4. Use Services

```python
# Get service from container
my_service = container.get(MyService)
my_service.do_something()

# Emit events (handlers will be called automatically)
event_bus = container.get(EventBus)
event_bus.publish("memory_log.stored", {"memory_log_id": 123})
```

## Service Scopes

- **SINGLETON**: One instance for the entire application lifetime (default)
- **TRANSIENT**: New instance created every time `get()` is called
- **SCOPED**: One instance per scope (e.g., per-request, per-project)

```python
from src.modules.core.di import service, ServiceScope

@service(scope=ServiceScope.SINGLETON)   # One instance
class SingletonService:
    pass

@service(scope=ServiceScope.TRANSIENT)   # New instance each time
class TransientService:
    pass
```

## Event Handler Priority

Handlers with higher priority are called first:

```python
@event_handler("memory_log.stored", priority=100)  # Called first
async def high_priority_handler(self, data):
    pass

@event_handler("memory_log.stored", priority=50)   # Called second
async def medium_priority_handler(self, data):
    pass

@event_handler("memory_log.stored", priority=0)    # Called last
async def low_priority_handler(self, data):
    pass
```

## Disabling Handlers

```python
@event_handler("debug.event", enabled=False)  # Won't be registered
async def disabled_handler(self, data):
    pass
```

## Benefits

✅ **Single Source of Truth**: All services registered in one place
✅ **Auto-Discovery**: Event handlers automatically found and registered
✅ **Dependency Resolution**: Services auto-injected via constructor
✅ **Testability**: Easy to mock dependencies
✅ **Clear Dependencies**: Explicit constructor parameters
✅ **Lifecycle Management**: Automatic initialization and shutdown

## Migration from Manual Registration

### Before (Manual):
```python
# In app.py
event_bus = EventBus()
logger = Logger("app")
my_service = MyService(event_bus, logger)

# Somewhere else
event_bus.subscribe("memory_log.stored", my_handler)
```

### After (DI Container):
```python
# In app.py
container = ServiceContainer()
container.register_singleton(EventBus, EventBus())
container.register_singleton(Logger, Logger("app"))
container.register_class(MyService)
container.register_class(MyEventHandlers)

await container.initialize_all()

# Event handlers auto-registered via decorators!
```

## API Reference

### ServiceContainer

- `register_singleton(type, instance)` - Register pre-created instance
- `register_factory(type, factory, scope)` - Register factory function
- `register_class(type, implementation, scope)` - Register class for auto-instantiation
- `get(type)` - Get service instance (creates if needed)
- `has(type)` - Check if service registered
- `get_all()` - Get all singleton instances
- `initialize_all()` - Initialize all services
- `shutdown_all()` - Shutdown all services gracefully

### EventListenerRegistry

- `register_handler(event_type, handler, ...)` - Register handler manually
- `discover_handlers(handler_classes)` - Auto-discover from class instances
- `subscribe_all()` - Subscribe all handlers to EventBus
- `unsubscribe_all()` - Unsubscribe all handlers
- `get_handlers_for_event(event_type)` - Get handlers for event
- `get_all_event_types()` - Get all registered event types
- `get_stats()` - Get handler statistics

### Decorators

- `@service(scope=ServiceScope.SINGLETON)` - Mark class as service
- `@event_handler(event_type, priority=0, enabled=True)` - Mark method as event handler
- `@injectable` - Mark function for dependency injection (future use)

## Examples

See `src/events/internal_handlers.py` (coming soon) for real-world examples.

# Event-Driven Architecture

## Structure

```
src/events/
├── __init__.py           # Package exports
├── schemas.py            # Event type definitions and Pydantic schemas
├── handlers.py           # Event handler registry
├── socket_handlers.py    # Socket.IO event handlers (organized by domain)
├── emitters.py          # Helper functions to emit events
└── README.md            # This file
```

## Key Components

### 1. Event Schemas (`schemas.py`)
- **EventType**: Centralized enum of all event types
- **SocketEvent**: Base event structure
- **Specific Event Models**: Typed schemas for each event (MemoryLogEvent, MentalNoteEvent, etc.)

### 2. Handler Registry (`handlers.py`)
- **EventHandlerRegistry**: Manages event handler registration and execution
- Supports decorator-based handler registration
- Automatic error handling and logging

### 3. Socket Handlers (`socket_handlers.py`)
- Organized by domain (connection, subscription, memory_logs, mental_notes)
- Each handler validates input using Pydantic schemas
- Handlers are automatically registered with the registry

### 4. Event Emitters (`emitters.py`)
- **EventEmitter**: Helper class with typed methods to emit events
- Ensures type safety and consistent event structure
- Used by business logic to emit events

## Usage Examples

### Adding a New Event Type

1. **Define the event type in `schemas.py`:**
```python
class EventType(str, Enum):
    # ... existing events ...
    MY_NEW_EVENT = "my_new_event"

class MyNewEventData(BaseModel):
    id: int
    name: str
    timestamp: datetime
```

2. **Create a handler in `socket_handlers.py`:**
```python
def register_my_feature_handlers(registry: EventHandlerRegistry, sio):
    @registry.register(EventType.MY_NEW_EVENT)
    async def handle_my_event(sid: str, data: Dict[str, Any], context):
        try:
            event_data = MyNewEventData(**data)
            # Handle the event
            context.logger.info(f"Received my_new_event from {sid}")
        except Exception as e:
            context.logger.error(f"Error: {e}")
            await sio.emit(EventType.ERROR.value, {'message': str(e)}, room=sid)

# Don't forget to call this in register_all_handlers()
```

3. **Add emitter method in `emitters.py`:**
```python
async def emit_my_new_event(self, data: Dict[str, Any], room: str = "my_room"):
    event_data = MyNewEventData(**data)
    event = SocketEvent(
        event_type=EventType.MY_NEW_EVENT,
        data=event_data.model_dump(),
        room=room
    )
    await self.socket_service.emit_event(event)
```

### Using in Routes

```python
from fastapi import APIRouter, Request

router = APIRouter()

@router.post("/memory-logs")
async def create_memory_log(data: dict, request: Request):
    # Your business logic
    memory_log = {
        'id': 123,
        'user_id': 1,
        'content': 'New memory log',
        'created_at': datetime.utcnow()
    }
    
    # Emit event to all subscribed clients
    await request.app.state.event_emitter.emit_memory_log_created(memory_log)
    
    return memory_log
```

### Client-Side Subscription (Next.js)

```typescript
// Subscribe to memory logs
socket.emit('subscribe_event', { event_type: 'memory_logs' });

// Listen for events
socket.on('memory_log_created', (data) => {
  console.log('New memory log:', data);
});

socket.on('memory_log_updated', (data) => {
  console.log('Updated memory log:', data);
});
```

## Event Flow

### Server → Client (Broadcasting)
```
Business Logic → EventEmitter → SocketService → Clients (in room)
```

### Client → Server (Handling)
```
Client → SocketIO → HandlerRegistry → Specific Handler → Response
```

## Benefits

1. **Type Safety**: All events are validated with Pydantic schemas
2. **Centralized**: All event types in one place (EventType enum)
3. **Organized**: Handlers grouped by domain/feature
4. **Scalable**: Easy to add new events and handlers
5. **Testable**: Handlers can be tested independently
6. **Maintainable**: Clear separation of concerns

## Testing

```python
# Test event emission
async def test_emit_memory_log():
    emitter = EventEmitter(socket_service)
    await emitter.emit_memory_log_created({
        'id': 1,
        'user_id': 1,
        'content': 'Test',
        'created_at': datetime.utcnow()
    })

# Test handler
async def test_ping_handler():
    registry = EventHandlerRegistry(logger)
    register_connection_handlers(registry, sio)
    
    await registry.handle_event(
        'ping',
        'test-sid',
        {'timestamp': 123456},
        context
    )
```

## Room Strategy

- **memory_logs**: All memory log events
- **mental_notes**: All mental note events
- **user_{user_id}**: User-specific events
- **admin**: Admin-only events

Clients subscribe to rooms they're interested in, reducing unnecessary traffic.

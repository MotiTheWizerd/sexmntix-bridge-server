# Event-Driven Architecture Guide

## 🏗️ Architecture Overview

Your socket system is now structured for scale with:

```
src/events/
├── schemas.py           → Event types & data models (single source of truth)
├── handlers.py          → Handler registry (automatic routing)
├── socket_handlers.py   → Event handlers (organized by domain)
├── emitters.py         → Type-safe event emitters
└── README.md           → Detailed documentation
```

## 🚀 Quick Usage

### 1. Emit Events from Your Routes

```python
from fastapi import APIRouter, Request

@router.post("/memory-logs")
async def create_memory_log(data: dict, request: Request):
    # Your business logic
    memory_log = {...}
    
    # Emit to all subscribers
    await request.app.state.event_emitter.emit_memory_log_created(memory_log)
    
    return memory_log
```

### 2. Client Subscribes & Listens

```typescript
// Subscribe to room
socket.emit('subscribe_event', { event_type: 'memory_logs' });

// Listen for events
socket.on('memory_log_created', (data) => {
  console.log('New log:', data);
});
```

## 📝 Adding New Events (3 Steps)

### Step 1: Define Event Type & Schema

```python
# src/events/schemas.py

class EventType(str, Enum):
    # Add your event
    TASK_COMPLETED = "task_completed"

class TaskCompletedEvent(BaseModel):
    task_id: int
    user_id: int
    completed_at: datetime
```

### Step 2: Create Handler (if needed for client → server)

```python
# src/events/socket_handlers.py

def register_task_handlers(registry: EventHandlerRegistry, sio):
    @registry.register(EventType.TASK_COMPLETED)
    async def handle_task_completed(sid: str, data: Dict[str, Any], context):
        event_data = TaskCompletedEvent(**data)
        context.logger.info(f"Task {event_data.task_id} completed")
        # Your logic here

# Add to register_all_handlers()
def register_all_handlers(registry: EventHandlerRegistry, sio):
    # ... existing ...
    register_task_handlers(registry, sio)
```

### Step 3: Add Emitter Method

```python
# src/events/emitters.py

async def emit_task_completed(self, task: Dict[str, Any], room: str = "tasks"):
    event_data = TaskCompletedEvent(**task)
    event = SocketEvent(
        event_type=EventType.TASK_COMPLETED,
        data=event_data.model_dump(),
        room=room
    )
    await self.socket_service.emit_event(event)
```

## 🎯 Event Flow Patterns

### Pattern 1: Broadcast to Room
```python
# Server emits to all subscribers in 'memory_logs' room
await event_emitter.emit_memory_log_created(log, room="memory_logs")
```

### Pattern 2: User-Specific Events
```python
# Server emits to specific user
await event_emitter.emit_memory_log_created(log, room=f"user_{user_id}")
```

### Pattern 3: Direct to Client
```python
# Server emits to specific socket connection
event = SocketEvent(
    event_type=EventType.NOTIFICATION,
    data={...},
    sid="socket-id-here"
)
await socket_service.emit_event(event)
```

### Pattern 4: Client Triggers Handler
```typescript
// Client emits event that triggers server handler
socket.emit('custom_action', { data: 'value' });
```

## 🏷️ Room Strategy

Organize clients into rooms for targeted messaging:

- `memory_logs` - All memory log events
- `mental_notes` - All mental note events  
- `user_{user_id}` - User-specific events
- `admin` - Admin-only broadcasts
- `notifications` - General notifications

```typescript
// Client subscribes to multiple rooms
socket.emit('subscribe_event', { event_type: 'memory_logs' });
socket.emit('subscribe_event', { event_type: 'user_123' });
```

## ✅ Benefits of This Architecture

1. **Type Safety**: Pydantic validates all events
2. **Centralized**: All event types in `EventType` enum
3. **Organized**: Handlers grouped by domain
4. **Scalable**: Add events without touching core code
5. **Testable**: Each handler can be tested independently
6. **Maintainable**: Clear separation of concerns

## 📊 Current Event Types

### Connection Events
- `connection_established` - Client connected
- `ping` / `pong` - Health check

### Subscription Events
- `subscribe_event` - Subscribe to room
- `unsubscribe_event` - Unsubscribe from room
- `subscribed` / `unsubscribed` - Confirmation

### Memory Log Events
- `memory_log_created`
- `memory_log_updated`
- `memory_log_deleted`

### Mental Note Events
- `mental_note_created`
- `mental_note_updated`
- `mental_note_deleted`

### User Events
- `user_status_changed`

### Error Events
- `error` - Error occurred

## 🧪 Testing

### Test Event Emission
```python
# tests/test_events.py
async def test_emit_event():
    emitter = EventEmitter(socket_service)
    await emitter.emit_memory_log_created({
        'id': 1,
        'user_id': 1,
        'content': 'Test',
        'created_at': datetime.utcnow()
    })
```

### Test Handler
```python
async def test_handler():
    registry = EventHandlerRegistry(logger)
    await registry.handle_event('ping', 'sid', {'timestamp': 123}, context)
```

## 🔧 Integration with EventBus

Your existing `EventBus` can trigger socket events:

```python
# In your service
event_bus.subscribe('memory_log.created', async_handler)

async def async_handler(event_data):
    await event_emitter.emit_memory_log_created(event_data)
```

## 📚 See Also

- `src/events/README.md` - Detailed technical documentation
- `src/api/routes/memory_logs_example.py` - Full working example
- `SOCKET_TESTING_GUIDE.md` - Testing guide
- `SOCKET_QUICK_START.md` - Quick start guide

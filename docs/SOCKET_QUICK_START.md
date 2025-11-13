# Socket.IO Quick Start

## ✅ What's Ready

### Python Server
- Socket.IO installed and configured
- Endpoint: `ws://localhost:8000/socket.io`
- Built-in events: `ping`, `subscribe_event`, `unsubscribe_event`

### Test Tools
- Python test script: `tests/socket_test.py`
- REST API test endpoint: `POST /api/socket-test/emit`

## 🚀 Quick Test (5 minutes)

### Step 1: Start Server
```bash
python main.py
```

### Step 2: Test from Python
```bash
python tests/socket_test.py
```

Expected output:
```
✅ Connected to server
✅ Connection established: {'sid': '...'}
📤 Sending ping...
✅ Pong received: {'timestamp': ...}
📤 Subscribing to 'memory_logs' events...
✅ Subscribed to: {'event_type': 'memory_logs'}
```

### Step 3: Test from Browser
Open browser console and paste:
```javascript
const socket = io('http://localhost:8000', { path: '/socket.io' });

socket.on('connect', () => console.log('✅ Connected'));
socket.on('connection_established', (data) => console.log('✅ Established:', data));
socket.on('pong', (data) => console.log('✅ Pong:', data));

// Send ping
socket.emit('ping', { timestamp: Date.now() });

// Subscribe to events
socket.emit('subscribe_event', { event_type: 'memory_logs' });
```

## 📦 Next.js Setup

### Install
```bash
npm install socket.io-client
```

### Minimal Example
```typescript
// app/page.tsx
'use client';
import { useEffect, useState } from 'react';
import { io } from 'socket.io-client';

export default function Home() {
  const [status, setStatus] = useState('disconnected');

  useEffect(() => {
    const socket = io('http://localhost:8000', { path: '/socket.io' });
    
    socket.on('connect', () => setStatus('connected'));
    socket.on('disconnect', () => setStatus('disconnected'));
    
    return () => { socket.disconnect(); };
  }, []);

  return <div>Socket Status: {status}</div>;
}
```

## 🔧 Trigger Events from REST API

```bash
# Emit to all clients
curl -X POST http://localhost:8000/api/socket-test/emit \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "test_event",
    "data": {"message": "Hello"}
  }'

# Emit to specific room
curl -X POST http://localhost:8000/api/socket-test/emit \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "memory_log_created",
    "room": "memory_logs",
    "data": {"id": 123, "content": "New log"}
  }'

# Quick test
curl http://localhost:8000/api/socket-test/trigger-test
```

## 📝 Event Schema Template

```typescript
// Define your events
interface SocketEvents {
  // Server → Client
  memory_log_created: { id: number; content: string; created_at: string };
  mental_note_updated: { id: number; title: string };
  
  // Client → Server
  subscribe_event: { event_type: string };
  ping: { timestamp: number };
}
```

## 🎯 Integration with Your EventBus

```python
# In your service/route, emit socket events
async def create_memory_log(data, request):
    # ... create log in database ...
    
    # Emit to subscribed clients
    await request.app.state.socket_service.emit_to_room(
        'memory_logs',
        'memory_log_created',
        {
            'id': log.id,
            'content': log.content,
            'created_at': log.created_at.isoformat()
        }
    )
```

## 📚 Full Documentation
See `SOCKET_TESTING_GUIDE.md` for complete examples and troubleshooting.

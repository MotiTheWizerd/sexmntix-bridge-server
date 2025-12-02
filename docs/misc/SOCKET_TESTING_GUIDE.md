# Socket.IO Testing Guide

## Overview
This guide covers testing Socket.IO connections between your Python FastAPI server and Next.js frontend using event-driven design.

## Server Setup (Python/FastAPI)

### Dependencies Installed
- `python-socketio` - Socket.IO server implementation

### Server Components Created
1. **SocketService** (`src/services/socket_service.py`)
   - Handles WebSocket connections
   - Manages rooms and subscriptions
   - Integrates with your EventBus

2. **Socket Endpoint**: `ws://localhost:8000/socket.io`

### Built-in Events
- `connect` - Client connects
- `disconnect` - Client disconnects
- `ping` - Health check (responds with `pong`)
- `subscribe_event` - Subscribe to specific event types
- `unsubscribe_event` - Unsubscribe from event types

## Client Setup (Next.js)

### Install Dependencies
```bash
npm install socket.io-client
# or
yarn add socket.io-client
# or
pnpm add socket.io-client
```

### Example Next.js Client Code

#### 1. Create Socket Hook (`hooks/useSocket.ts`)
```typescript
import { useEffect, useState } from 'react';
import { io, Socket } from 'socket.io-client';

export const useSocket = (url: string = 'http://localhost:8000') => {
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    const socketInstance = io(url, {
      path: '/socket.io',
      transports: ['websocket', 'polling'],
    });

    socketInstance.on('connect', () => {
      console.log('✅ Connected to server');
      setIsConnected(true);
    });

    socketInstance.on('connection_established', (data) => {
      console.log('✅ Connection established:', data);
    });

    socketInstance.on('disconnect', () => {
      console.log('❌ Disconnected from server');
      setIsConnected(false);
    });

    socketInstance.on('pong', (data) => {
      console.log('✅ Pong received:', data);
    });

    setSocket(socketInstance);

    return () => {
      socketInstance.disconnect();
    };
  }, [url]);

  return { socket, isConnected };
};
```

#### 2. Use in Component (`components/SocketTest.tsx`)
```typescript
'use client';

import { useSocket } from '@/hooks/useSocket';
import { useEffect } from 'react';

export default function SocketTest() {
  const { socket, isConnected } = useSocket();

  useEffect(() => {
    if (!socket) return;

    // Subscribe to events
    socket.on('subscribed', (data) => {
      console.log('✅ Subscribed:', data);
    });

    socket.on('memory_logs', (data) => {
      console.log('📨 Memory log event:', data);
    });

    return () => {
      socket.off('subscribed');
      socket.off('memory_logs');
    };
  }, [socket]);

  const handlePing = () => {
    if (socket) {
      socket.emit('ping', { timestamp: Date.now() });
    }
  };

  const handleSubscribe = () => {
    if (socket) {
      socket.emit('subscribe_event', { event_type: 'memory_logs' });
    }
  };

  return (
    <div className="p-4">
      <h2 className="text-2xl font-bold mb-4">Socket.IO Test</h2>
      
      <div className="mb-4">
        Status: {isConnected ? '🟢 Connected' : '🔴 Disconnected'}
      </div>

      <div className="space-x-2">
        <button
          onClick={handlePing}
          disabled={!isConnected}
          className="px-4 py-2 bg-blue-500 text-white rounded disabled:bg-gray-300"
        >
          Send Ping
        </button>

        <button
          onClick={handleSubscribe}
          disabled={!isConnected}
          className="px-4 py-2 bg-green-500 text-white rounded disabled:bg-gray-300"
        >
          Subscribe to Memory Logs
        </button>
      </div>
    </div>
  );
}
```

#### 3. Add to Page (`app/test/page.tsx`)
```typescript
import SocketTest from '@/components/SocketTest';

export default function TestPage() {
  return <SocketTest />;
}
```

## Testing Steps

### 1. Test Python Server
```bash
# Start the server
python main.py

# In another terminal, run the test script
python tests/socket_test.py
```

### 2. Test Next.js Client
```bash
# Make sure Python server is running
# Then start Next.js dev server
npm run dev

# Navigate to http://localhost:3000/test
# Open browser console to see connection logs
```

### 3. Test Event Flow

#### Server → Client
```python
# In your Python code, emit events to clients
await app.state.socket_service.emit_to_room(
    'memory_logs',
    'memory_log_created',
    {'id': 123, 'content': 'New memory log'}
)
```

#### Client → Server
```typescript
// In your Next.js code
socket.emit('custom_event', { data: 'your data' });
```

## Event Schema Examples

### Ping/Pong
```typescript
// Client → Server
{ timestamp: number }

// Server → Client
{ timestamp: number }
```

### Subscribe/Unsubscribe
```typescript
// Client → Server
{ event_type: string }

// Server → Client
{ event_type: string }
```

### Custom Events (Example)
```typescript
// Memory Log Created
{
  id: number,
  user_id: number,
  content: string,
  created_at: string
}
```

## Troubleshooting

### Connection Issues
- Verify server is running on port 8000
- Check CORS settings (currently set to allow all origins)
- Ensure firewall allows WebSocket connections
- Check browser console for errors

### Event Not Received
- Verify event name matches exactly (case-sensitive)
- Check if client is subscribed to the room
- Verify socket is connected before emitting
- Check server logs for errors

### Performance
- Use rooms for targeted messaging
- Avoid emitting large payloads
- Consider message throttling for high-frequency events

## Next Steps

1. Define your event schemas in a shared types file
2. Add authentication to socket connections
3. Implement reconnection logic with exponential backoff
4. Add event validation using Pydantic models
5. Set up monitoring for socket connections
6. Add rate limiting for socket events

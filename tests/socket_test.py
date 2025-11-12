"""
Socket.IO test script for Python server
Run this to test socket connection from Python client
"""
import asyncio
import socketio


async def test_socket_connection():
    sio = socketio.AsyncClient()
    
    @sio.event
    async def connect():
        print("✅ Connected to server")
    
    @sio.event
    async def connection_established(data):
        print(f"✅ Connection established: {data}")
    
    @sio.event
    async def pong(data):
        print(f"✅ Pong received: {data}")
    
    @sio.event
    async def subscribed(data):
        print(f"✅ Subscribed to: {data}")
    
    @sio.event
    async def memory_log_created(data):
        print(f"📨 Memory log created event: {data}")
    
    @sio.event
    async def mental_note_created(data):
        print(f"📨 Mental note created event: {data}")
    
    @sio.event
    async def error(data):
        print(f"❌ Error event: {data}")
    
    @sio.event
    async def disconnect():
        print("❌ Disconnected from server")
    
    try:
        # Connect to server
        await sio.connect('http://localhost:8000', socketio_path='/socket.io')
        print("Waiting for connection_established event...")
        await asyncio.sleep(1)
        
        # Test ping/pong
        print("\n📤 Sending ping...")
        await sio.emit('ping', {'timestamp': asyncio.get_event_loop().time()})
        await asyncio.sleep(1)
        
        # Test subscription to memory_logs
        print("\n📤 Subscribing to 'memory_logs' events...")
        await sio.emit('subscribe_event', {'event_type': 'memory_logs'})
        await asyncio.sleep(1)
        
        # Test subscription to mental_notes
        print("\n📤 Subscribing to 'mental_notes' events...")
        await sio.emit('subscribe_event', {'event_type': 'mental_notes'})
        await asyncio.sleep(1)
        
        # Keep connection alive to receive events
        print("\n⏳ Listening for events (10 seconds)...")
        print("💡 Tip: Trigger events via REST API:")
        print("   POST http://localhost:8000/api/memory-logs-example")
        await asyncio.sleep(10)
        
        # Disconnect
        await sio.disconnect()
        print("\n✅ Test completed successfully")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_socket_connection())

"""
Socket test endpoint - trigger socket events from REST API
"""
from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from typing import Dict, Any

router = APIRouter(prefix="/api/socket-test", tags=["socket-test"])


class EmitEventRequest(BaseModel):
    event_type: str
    room: str | None = None
    data: Dict[str, Any]


@router.post("/emit")
async def emit_socket_event(request: Request, payload: EmitEventRequest):
    """
    Emit a socket event for testing
    
    Example:
    POST /api/socket-test/emit
    {
        "event_type": "test_event",
        "room": "memory_logs",
        "data": {"message": "Hello from REST API"}
    }
    """
    socket_service = request.app.state.socket_service
    
    if payload.room:
        await socket_service.emit_to_room(payload.room, payload.event_type, payload.data)
        return {
            "status": "success",
            "message": f"Event '{payload.event_type}' emitted to room '{payload.room}'"
        }
    else:
        await socket_service.emit_to_all(payload.event_type, payload.data)
        return {
            "status": "success",
            "message": f"Event '{payload.event_type}' emitted to all clients"
        }


@router.get("/trigger-test")
async def trigger_test_event(request: Request):
    """
    Quick test endpoint to trigger a test event
    """
    socket_service = request.app.state.socket_service
    
    await socket_service.emit_to_all('test_event', {
        'message': 'This is a test event from REST API',
        'timestamp': 'now'
    })
    
    return {
        "status": "success",
        "message": "Test event emitted to all connected clients"
    }

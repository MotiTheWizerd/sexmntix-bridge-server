"""
Example: Memory logs route with socket event emission
This shows how to integrate socket events with your REST API
"""
from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import Optional

router = APIRouter(prefix="/api/memory-logs-example", tags=["memory-logs-example"])


class CreateMemoryLogRequest(BaseModel):
    user_id: int
    content: str


class UpdateMemoryLogRequest(BaseModel):
    content: str


@router.post("/")
async def create_memory_log(data: CreateMemoryLogRequest, request: Request):
    """
    Create a memory log and emit socket event to subscribers
    """
    # Simulate creating in database
    memory_log = {
        'id': 123,  # Would come from database
        'user_id': data.user_id,
        'content': data.content,
        'created_at': datetime.utcnow()
    }
    
    # Emit socket event to all clients subscribed to 'memory_logs' room
    await request.app.state.event_emitter.emit_memory_log_created(memory_log)
    
    return {
        'status': 'success',
        'data': memory_log,
        'message': 'Memory log created and event emitted'
    }


@router.put("/{log_id}")
async def update_memory_log(log_id: int, data: UpdateMemoryLogRequest, request: Request):
    """
    Update a memory log and emit socket event to subscribers
    """
    # Simulate updating in database
    memory_log = {
        'id': log_id,
        'user_id': 1,  # Would come from database
        'content': data.content,
        'created_at': datetime.utcnow(),
        'updated_at': datetime.utcnow()
    }
    
    # Emit socket event
    await request.app.state.event_emitter.emit_memory_log_updated(memory_log)
    
    return {
        'status': 'success',
        'data': memory_log,
        'message': 'Memory log updated and event emitted'
    }


@router.delete("/{log_id}")
async def delete_memory_log(log_id: int, request: Request):
    """
    Delete a memory log and emit socket event to subscribers
    """
    # Simulate deleting from database
    
    # Emit socket event
    await request.app.state.event_emitter.emit_memory_log_deleted(log_id)
    
    return {
        'status': 'success',
        'message': f'Memory log {log_id} deleted and event emitted'
    }


@router.post("/{log_id}/notify-user")
async def notify_specific_user(log_id: int, user_id: int, request: Request):
    """
    Send event to specific user only (using user-specific room)
    """
    memory_log = {
        'id': log_id,
        'user_id': user_id,
        'content': 'This is a private notification',
        'created_at': datetime.utcnow()
    }
    
    # Emit to user-specific room
    await request.app.state.event_emitter.emit_memory_log_created(
        memory_log,
        room=f"user_{user_id}"
    )
    
    return {
        'status': 'success',
        'message': f'Notification sent to user {user_id}'
    }

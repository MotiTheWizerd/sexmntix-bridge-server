"""
Event schemas and types for socket communication
"""
from pydantic import BaseModel, Field
from typing import Any, Dict, Optional
from datetime import datetime
from enum import Enum


class EventType(str, Enum):
    """Centralized event type definitions"""
    # Connection events
    CONNECTION_ESTABLISHED = "connection_established"
    PING = "ping"
    PONG = "pong"
    
    # Subscription events
    SUBSCRIBE = "subscribe_event"
    UNSUBSCRIBE = "unsubscribe_event"
    SUBSCRIBED = "subscribed"
    UNSUBSCRIBED = "unsubscribed"
    
    # Memory log events
    MEMORY_LOG_CREATED = "memory_log_created"
    MEMORY_LOG_UPDATED = "memory_log_updated"
    MEMORY_LOG_DELETED = "memory_log_deleted"
    
    # Mental note events
    MENTAL_NOTE_CREATED = "mental_note_created"
    MENTAL_NOTE_UPDATED = "mental_note_updated"
    MENTAL_NOTE_DELETED = "mental_note_deleted"
    
    # User events
    USER_STATUS_CHANGED = "user_status_changed"
    
    # Error events
    ERROR = "error"


class SocketEvent(BaseModel):
    """Base event schema"""
    event_type: EventType
    data: Dict[str, Any]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    room: Optional[str] = None
    sid: Optional[str] = None


# Specific event schemas
class PingEvent(BaseModel):
    timestamp: float


class PongEvent(BaseModel):
    timestamp: float


class SubscriptionEvent(BaseModel):
    event_type: str


class MemoryLogEvent(BaseModel):
    id: int
    user_id: int
    content: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class MentalNoteEvent(BaseModel):
    id: int
    user_id: int
    title: str
    content: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class UserStatusEvent(BaseModel):
    user_id: int
    status: str
    timestamp: datetime


class ErrorEvent(BaseModel):
    message: str
    code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

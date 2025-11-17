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

    # XCP (MCP) Server events
    MCP_SERVERS_INITIALIZED = "initialize_mcp_servers"
    XCP_SERVER_STARTED = "xcp_server_started"
    XCP_SERVER_STOPPED = "xcp_server_stopped"
    XCP_SESSION_STARTED = "xcp_session_started"
    XCP_SESSION_ENDED = "xcp_session_ended"
    XCP_TOOL_CALLED = "xcp_tool_called"
    XCP_TOOL_COMPLETED = "xcp_tool_completed"
    XCP_TOOL_FAILED = "xcp_tool_failed"
    XCP_RESOURCE_ACCESSED = "xcp_resource_accessed"

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
    id: str
    user_id: str
    content: str
    created_at: datetime
    updated_at: Optional[datetime] = None


class MentalNoteEvent(BaseModel):
    id: str
    user_id: str
    title: str
    content: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class UserStatusEvent(BaseModel):
    user_id: str
    status: str
    timestamp: datetime


class ErrorEvent(BaseModel):
    message: str
    code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class XCPToolEvent(BaseModel):
    """Event for XCP tool calls"""
    tool_name: str
    user_id: str
    project_id: str
    arguments: Dict[str, Any]
    session_id: Optional[str] = None


class XCPToolCompletedEvent(BaseModel):
    """Event for successful XCP tool completion"""
    tool_name: str
    user_id: str
    project_id: str
    result: Any
    duration_ms: float
    session_id: Optional[str] = None


class XCPToolFailedEvent(BaseModel):
    """Event for failed XCP tool execution"""
    tool_name: str
    user_id: str
    project_id: str
    error_message: str
    error_code: Optional[str] = None
    session_id: Optional[str] = None


class XCPSessionEvent(BaseModel):
    """Event for XCP session lifecycle"""
    session_id: str
    client_info: Optional[Dict[str, Any]] = None


class XCPResourceEvent(BaseModel):
    """Event for XCP resource access"""
    resource_uri: str
    user_id: str
    project_id: str
    session_id: Optional[str] = None

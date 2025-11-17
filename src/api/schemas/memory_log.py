from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Dict, Any, Optional, List


class MemoryLogData(BaseModel):
    """Nested memory log data structure - all fields are optional"""
    content: Optional[str] = None
    task: Optional[str] = None
    agent: Optional[str] = "mcp_client"
    tags: Optional[List[str]] = []
    metadata: Optional[Dict[str, Any]] = {}

    model_config = {"extra": "allow"}


class MemoryLogCreate(BaseModel):
    """New unified format for memory log creation

    Format:
    {
        "user_id": "uuid-string",
        "project_id": "default",
        "memory_log": {
            "content": "...",
            "task": "...",
            "agent": "...",
            "tags": [...],
            "metadata": {...}
        }
    }

    The system will automatically add a datetime field.
    """
    user_id: str
    project_id: str
    memory_log: MemoryLogData


class MemoryLogResponse(BaseModel):
    id: str
    task: str
    agent: str
    date: datetime
    raw_data: Dict[str, Any]
    embedding: Optional[List[float]] = None
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MemoryLogSearchRequest(BaseModel):
    query: str
    user_id: str  # Required: UUID from users table
    project_id: Optional[str] = "default"  # Default project_id if not provided
    limit: Optional[int] = 10
    min_similarity: Optional[float] = 0.0
    filters: Optional[Dict[str, Any]] = None
    tag: Optional[str] = None  # Filter by individual tag (e.g., "chromadb")


class MemoryLogSearchResult(BaseModel):
    id: str
    memory_log_id: Optional[str] = None
    document: Dict[str, Any]
    metadata: Dict[str, Any]
    distance: float
    similarity: float

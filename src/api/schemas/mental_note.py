from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any, Optional, List


class MentalNoteCreate(BaseModel):
    """Schema for creating mental notes with optional user/project isolation"""
    model_config = {"extra": "allow"}

    sessionId: str
    startTime: int
    user_id: Optional[str] = "1"  # Default user_id for backward compatibility
    project_id: Optional[str] = "default"  # Default project_id


class MentalNoteResponse(BaseModel):
    id: int
    session_id: str
    start_time: int
    raw_data: Dict[str, Any]
    embedding: Optional[List[float]] = None
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MentalNoteSearchRequest(BaseModel):
    """Schema for semantic search of mental notes"""
    query: str
    session_id: Optional[str] = None  # Filter by specific session
    user_id: Optional[str] = "1"  # Default user_id if not provided
    project_id: Optional[str] = "default"  # Default project_id if not provided
    limit: Optional[int] = 10
    min_similarity: Optional[float] = 0.0
    note_type: Optional[str] = None  # Filter by note_type if provided


class MentalNoteSearchResult(BaseModel):
    """Result from semantic search with similarity scores"""
    id: str
    mental_note_id: Optional[int] = None
    document: Dict[str, Any]
    metadata: Dict[str, Any]
    distance: float
    similarity: float

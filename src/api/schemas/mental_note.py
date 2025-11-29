from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any, Optional, List


class MentalNoteCreate(BaseModel):
    """Schema for creating mental notes with optional user/project isolation"""
    model_config = {"extra": "allow"}

    sessionId: Optional[str] = None
    content: str
    note_type: str = "note"
    user_id: str  # Required: UUID from users table
    project_id: Optional[str] = "default"  # Default project_id
    meta_data: Optional[Dict[str, Any]] = {}


class MentalNoteResponse(BaseModel):
    id: str
    session_id: Optional[str]
    content: str
    note_type: str
    meta_data: Dict[str, Any]
    embedding: Optional[List[float]] = None
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class MentalNoteSearchRequest(BaseModel):
    """Schema for semantic search of mental notes"""
    model_config = {
        "json_schema_extra": {
            "example": {
                "query": "claude cli",
                "user_id": "84e17260-ff03-409b-bf30-0b5ba52a2ab4",
                "project_id": "08fd3ab5-215c-4405-a5b6-17b2620e064",
                "limit": 1
            }
        }
    }

    query: str
    session_id: Optional[str] = None  # Filter by specific session
    user_id: str  # Required: UUID from users table
    project_id: Optional[str] = "default"  # Default project_id if not provided
    limit: Optional[int] = 5
    min_similarity: Optional[float] = 0.8
    note_type: Optional[str] = None  # Filter by note_type if provided
    format: Optional[str] = "json"  # Response format: 'json' or 'text'


class MentalNoteSearchResult(BaseModel):
    """Result from semantic search with similarity scores"""
    id: str
    mental_note_id: Optional[str] = None
    document: Dict[str, Any]
    metadata: Dict[str, Any]
    distance: float
    similarity: float

"""
Pydantic schemas for conversation API endpoints.

Defines request/response models for conversation operations.
"""

from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Dict, Any, Optional, List
import uuid


class ConversationMessage(BaseModel):
    """
    Single message in a conversation.

    Attributes:
        role: Speaker role (e.g., "user", "assistant", "system")
        message_id: Unique identifier for the message (auto-generated if not provided)
        text: Message content
    """
    role: str
    message_id: Optional[str] = None
    text: str

    @field_validator('message_id', mode='before')
    @classmethod
    def generate_message_id(cls, v):
        """Auto-generate message_id if not provided"""
        if v is None or v == '':
            return str(uuid.uuid4())
        return v


class ConversationCreate(BaseModel):
    """
    Schema for creating a new conversation.

    Storage structure: user_id/conversations/{conversation_id}/
    Note: project_id is deprecated and ignored (kept for backward compatibility only)

    Format:
    {
        "user_id": "1",
        "conversation_id": "691966a7-318c-8331-b3d0-9862429577c0",
        "model": "gpt-5-1-instant",
        "conversation": [
            {
                "role": "user",
                "message_id": "64ae03ed-597b-4368-aed3-1d1ab6c7745e",
                "text": "one more test"
            },
            {
                "role": "assistant",
                "message_id": "b5e7ff53-3d91-4e6a-bd41-d2fd5e96c937",
                "text": "received."
            }
        ]
    }
    """
    user_id: str  # Required: UUID from users table
    project_id: Optional[str] = None  # Deprecated: ignored, kept for backward compatibility
    conversation_id: str
    model: str
    conversation: List[ConversationMessage]
    session_id: Optional[str] = None  # Optional: Session identifier for grouping conversations


class ConversationResponse(BaseModel):
    """
    Response schema for conversation operations.

    Note: Embeddings are stored only in ChromaDB, not returned in API responses.
    """
    id: str
    conversation_id: str
    model: str
    raw_data: Dict[str, Any]
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    session_id: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationSearchRequest(BaseModel):
    """
    Schema for semantic search of conversations.

    Searches within user_id/conversations/ structure.
    Note: project_id is deprecated and ignored (kept for backward compatibility only)
    """
    query: str
    user_id: str  # Required: UUID from users table
    project_id: Optional[str] = None  # Deprecated: ignored, kept for backward compatibility
    limit: Optional[int] = 10
    min_similarity: Optional[float] = 0.0
    model: Optional[str] = None  # Filter by specific AI model
    session_id: Optional[str] = None  # Filter by session identifier


class ConversationSearchResult(BaseModel):
    """
    Result from semantic search.

    Includes document data, metadata, and similarity scores.
    """
    id: str
    conversation_id: Optional[str] = None
    document: Dict[str, Any]
    metadata: Dict[str, Any]
    distance: float
    similarity: float

from typing import Any, List, Optional
from pydantic import BaseModel, Field


class WorldViewResponse(BaseModel):
    user_id: str
    project_id: str
    session_id: Optional[str] = None
    conversation_count: Optional[int] = None
    is_first_conversation: Optional[bool] = None
    recent_conversations: List[Any] = Field(default_factory=list)
    # Kept for compatibility; will be empty when not used
    recent_memory_logs: List[Any] = Field(default_factory=list)
    recent_mental_notes: List[Any] = Field(default_factory=list)
    short_term_memory: Optional[str] = None
    is_cached: bool = False
    generated_at: str

    class Config:
        orm_mode = True

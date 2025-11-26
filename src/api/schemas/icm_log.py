from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field


class IcmLogResponse(BaseModel):
    id: str
    request_id: Optional[str] = None
    icm_type: str
    query: Optional[str] = None
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    session_id: Optional[str] = None
    retrieval_strategy: Optional[str] = None
    required_memory: Optional[Any] = None
    time_window_start: Optional[datetime] = None
    time_window_end: Optional[datetime] = None
    confidence: Optional[float] = Field(None, description="ICM-provided confidence score if available")
    payload: Optional[Any] = None
    results_count: Optional[int] = None
    limit: Optional[int] = None
    min_similarity: Optional[float] = None
    created_at: datetime

    class Config:
        orm_mode = True

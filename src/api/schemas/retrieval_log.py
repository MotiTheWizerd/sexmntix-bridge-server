from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel


class RetrievalLogResponse(BaseModel):
    id: str
    request_id: Optional[str] = None
    query: Optional[str] = None
    user_id: Optional[str] = None
    project_id: Optional[str] = None
    session_id: Optional[str] = None
    required_memory: Optional[Any] = None
    results: Optional[Any] = None
    results_count: Optional[int] = None
    limit: Optional[int] = None
    min_similarity: Optional[float] = None
    target: Optional[str] = None
    created_at: datetime

    class Config:
        orm_mode = True

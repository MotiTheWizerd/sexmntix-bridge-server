from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Dict, Any, Optional, List


class MemoryLogCreate(BaseModel):
    # Accept any JSON structure
    model_config = {"extra": "allow"}

    task: str
    agent: str
    date: str | datetime

    # User and project isolation for ChromaDB collections
    user_id: Optional[str] = None
    project_id: Optional[str] = None

    @field_validator("date", mode="before")
    @classmethod
    def parse_date(cls, v):
        if isinstance(v, str):
            # Handle date strings without time
            if "T" not in v:
                v = f"{v}T00:00:00"
            return datetime.fromisoformat(v)
        return v


class MemoryLogResponse(BaseModel):
    id: int
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
    user_id: str
    project_id: str
    limit: Optional[int] = 10
    min_similarity: Optional[float] = 0.0
    filters: Optional[Dict[str, Any]] = None


class MemoryLogSearchResult(BaseModel):
    id: str
    memory_log_id: Optional[int] = None
    document: Dict[str, Any]
    metadata: Dict[str, Any]
    distance: float
    similarity: float

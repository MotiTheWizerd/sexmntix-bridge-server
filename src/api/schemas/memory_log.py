from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Dict, Any


class MemoryLogCreate(BaseModel):
    # Accept any JSON structure
    model_config = {"extra": "allow"}
    
    task: str
    agent: str
    date: str | datetime
    
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
    created_at: datetime

    class Config:
        from_attributes = True

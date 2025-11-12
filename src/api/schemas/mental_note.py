from pydantic import BaseModel
from datetime import datetime
from typing import Dict, Any


class MentalNoteCreate(BaseModel):
    model_config = {"extra": "allow"}
    
    sessionId: str
    startTime: int


class MentalNoteResponse(BaseModel):
    id: int
    session_id: str
    start_time: int
    raw_data: Dict[str, Any]
    created_at: datetime

    class Config:
        from_attributes = True

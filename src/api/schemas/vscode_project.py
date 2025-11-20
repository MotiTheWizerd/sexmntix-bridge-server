from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional

class VscodeProjectBase(BaseModel):
    project_name: Optional[str] = None

class VscodeProjectCreate(VscodeProjectBase):
    user_id: str

class VscodeProjectResponse(VscodeProjectBase):
    id: str
    user_id: str
    created_at: datetime

    class Config:
        from_attributes = True

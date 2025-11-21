from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional

class UserProjectBase(BaseModel):
    project_name: Optional[str] = None

class UserProjectCreate(UserProjectBase):
    user_id: str

class UserProjectUpdate(BaseModel):
    project_name: Optional[str] = None

class UserProjectResponse(UserProjectBase):
    id: str
    user_id: str
    created_at: datetime

    class Config:
        from_attributes = True

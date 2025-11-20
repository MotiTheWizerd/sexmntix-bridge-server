from pydantic import BaseModel, UUID4
from datetime import datetime
from typing import Optional
from src.database.models.enums import ProjectType

class UserProjectBase(BaseModel):
    project_name: Optional[str] = None
    project_type: ProjectType = ProjectType.VSCODE

class UserProjectCreate(UserProjectBase):
    user_id: str

class UserProjectUpdate(BaseModel):
    project_name: Optional[str] = None
    project_type: Optional[ProjectType] = None

class UserProjectResponse(UserProjectBase):
    id: str
    user_id: str
    created_at: datetime

    class Config:
        from_attributes = True

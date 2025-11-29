from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .user_project import UserProjectResponse


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    display_name: str


class UserResponse(BaseModel):
    id: str  # UUID format
    email: str
    first_name: str
    last_name: str
    display_name: str
    created_at: datetime
    project_count: Optional[int] = None
    projects: Optional[List['UserProjectResponse']] = None

    class Config:
        from_attributes = True


# Resolve forward references after UserProjectResponse is defined
def _resolve_forward_refs():
    from .user_project import UserProjectResponse
    UserResponse.model_rebuild(_types_namespace={"UserProjectResponse": UserProjectResponse})


_resolve_forward_refs()

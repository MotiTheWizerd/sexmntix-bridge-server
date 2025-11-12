from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    first_name: str
    last_name: str
    display_name: str


class UserResponse(BaseModel):
    id: int
    email: str
    first_name: str
    last_name: str
    display_name: str
    created_at: datetime

    class Config:
        from_attributes = True

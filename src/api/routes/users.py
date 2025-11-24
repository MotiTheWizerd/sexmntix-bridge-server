from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import bcrypt
from src.api.dependencies.database import get_db_session
from src.api.dependencies.event_bus import get_event_bus
from src.api.dependencies.logger import get_logger
from src.api.schemas.user import UserCreate, UserResponse
from src.database.repositories import UserRepository
from src.modules.core import EventBus, Logger

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserResponse, status_code=201)
async def create_user(
    data: UserCreate,
    db: AsyncSession = Depends(get_db_session),
    event_bus: EventBus = Depends(get_event_bus),
    logger: Logger = Depends(get_logger),
):
    logger.info(f"Creating user: {data.email}")
    
    repo = UserRepository(db)
    
    # Check if user already exists
    existing_user = await repo.get_by_email(data.email)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Hash password (truncate to 72 bytes for bcrypt)
    password_bytes = data.password.encode('utf-8')[:72]
    password_hash = bcrypt.hashpw(password_bytes, bcrypt.gensalt()).decode('utf-8')
    
    user = await repo.create(
        email=data.email,
        password_hash=password_hash,
        first_name=data.first_name,
        last_name=data.last_name,
        display_name=data.display_name,
    )
    
    event_bus.publish("user.created", {"id": user.id, "email": data.email})
    logger.info(f"User created with id: {user.id}")
    
    return user


@router.get("/{id}", response_model=UserResponse)
async def get_user(
    id: str,
    db: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
):
    logger.info(f"Fetching user: {id}")
    
    repo = UserRepository(db)
    user = await repo.get_by_id(id)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.get("", response_model=List[UserResponse])
async def list_users(
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
):
    logger.info(f"Listing users (limit: {limit})")
    
    repo = UserRepository(db)
    users = await repo.get_all(limit=limit)
    
    return users

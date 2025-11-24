from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from src.api.dependencies.database import get_db_session
from src.api.dependencies.logger import get_logger
from src.api.schemas.user_project import UserProjectCreate, UserProjectUpdate, UserProjectResponse
from src.database.repositories import UserProjectRepository
from src.modules.core import Logger

router = APIRouter(prefix="/user-projects", tags=["user-projects"])

@router.get("", response_model=List[UserProjectResponse])
async def get_all_user_projects(
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
):
    logger.info(f"Fetching all user projects (limit: {limit})")

    repo = UserProjectRepository(db)
    projects = await repo.get_all(limit=limit)

    return projects

@router.post("", response_model=UserProjectResponse, status_code=201)
async def create_user_project(
    data: UserProjectCreate,
    db: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
):
    logger.info(f"Creating user project for user: {data.user_id}")

    repo = UserProjectRepository(db)
    project = await repo.create(
        user_id=data.user_id,
        project_name=data.project_name
    )

    logger.info(f"User project created with id: {project.id}")
    return project

@router.get("/user/{user_id}", response_model=List[UserProjectResponse])
async def get_user_projects_by_user(
    user_id: str,
    db: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
):
    logger.info(f"Fetching user projects for user: {user_id}")

    repo = UserProjectRepository(db)
    projects = await repo.get_by_user_id(user_id)

    return projects

@router.get("/{id}", response_model=UserProjectResponse)
async def get_user_project(
    id: str,
    db: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
):
    logger.info(f"Fetching user project: {id}")

    repo = UserProjectRepository(db)
    project = await repo.get_by_id(id)

    if not project:
        raise HTTPException(status_code=404, detail="User project not found")

    return project

@router.patch("/{id}", response_model=UserProjectResponse)
async def update_user_project(
    id: str,
    data: UserProjectUpdate,
    db: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
):
    logger.info(f"Updating user project: {id}")

    repo = UserProjectRepository(db)

    # Filter out None values to only update provided fields
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    project = await repo.update(id, **update_data)

    if not project:
        raise HTTPException(status_code=404, detail="User project not found")

    logger.info(f"User project updated: {id}")
    return project

@router.delete("/{id}", status_code=204)
async def delete_user_project(
    id: str,
    db: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
):
    logger.info(f"Deleting user project: {id}")

    repo = UserProjectRepository(db)
    deleted = await repo.delete(id)

    if not deleted:
        raise HTTPException(status_code=404, detail="User project not found")

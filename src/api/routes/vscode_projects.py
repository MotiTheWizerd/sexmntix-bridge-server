from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
from src.api.dependencies.database import get_db_session
from src.api.dependencies.logger import get_logger
from src.api.schemas.vscode_project import VscodeProjectCreate, VscodeProjectResponse
from src.database.repositories.vscode_project_repository import VscodeProjectRepository
from src.modules.core import Logger

router = APIRouter(prefix="/vscode-projects", tags=["vscode-projects"])

@router.post("", response_model=VscodeProjectResponse, status_code=201)
async def create_vscode_project(
    data: VscodeProjectCreate,
    db: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
):
    logger.info(f"Creating vscode project for user: {data.user_id}")
    
    repo = VscodeProjectRepository(db)
    project = await repo.create(
        user_id=data.user_id,
        project_name=data.project_name
    )
    
    logger.info(f"Vscode project created with id: {project.id}")
    return project

@router.get("/user/{user_id}", response_model=List[VscodeProjectResponse])
async def get_vscode_projects_by_user(
    user_id: str,
    db: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
):
    logger.info(f"Fetching vscode projects for user: {user_id}")
    
    repo = VscodeProjectRepository(db)
    projects = await repo.get_by_user_id(user_id)
    
    return projects

@router.get("/{id}", response_model=VscodeProjectResponse)
async def get_vscode_project(
    id: str,
    db: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
):
    logger.info(f"Fetching vscode project: {id}")
    
    repo = VscodeProjectRepository(db)
    project = await repo.get_by_id(id)
    
    if not project:
        raise HTTPException(status_code=404, detail="Vscode project not found")
    
    return project

@router.delete("/{id}", status_code=204)
async def delete_vscode_project(
    id: str,
    db: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
):
    logger.info(f"Deleting vscode project: {id}")
    
    repo = VscodeProjectRepository(db)
    deleted = await repo.delete(id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Vscode project not found")

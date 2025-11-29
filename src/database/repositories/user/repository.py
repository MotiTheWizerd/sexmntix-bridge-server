from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from src.database.models import User, UserProject
from ..base.base_repository import BaseRepository
from typing import Optional, List


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_by_id_with_project_count(self, user_id: str) -> Optional[dict]:
        """Get user by ID with project count"""
        result = await self.session.execute(
            select(
                User,
                func.count(UserProject.id).label('project_count')
            )
            .outerjoin(UserProject, User.id == UserProject.user_id)
            .where(User.id == user_id)
            .group_by(User.id)
        )
        row = result.first()
        if not row:
            return None
        
        user, project_count = row
        user_dict = {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "display_name": user.display_name,
            "created_at": user.created_at,
            "project_count": project_count
        }
        return user_dict
    
    async def get_all_with_project_count(self, limit: int = 100) -> List[dict]:
        """Get all users with project counts"""
        result = await self.session.execute(
            select(
                User,
                func.count(UserProject.id).label('project_count')
            )
            .outerjoin(UserProject, User.id == UserProject.user_id)
            .group_by(User.id)
            .limit(limit)
        )
        
        users = []
        for row in result:
            user, project_count = row
            user_dict = {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "display_name": user.display_name,
                "created_at": user.created_at,
                "project_count": project_count
            }
            users.append(user_dict)
        
        return users
    
    async def get_by_id_with_projects(self, user_id: str) -> Optional[dict]:
        """Get user by ID with full project details"""
        # Get user
        user_result = await self.session.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            return None
        
        # Get projects for this user
        projects_result = await self.session.execute(
            select(UserProject).where(UserProject.user_id == user_id)
        )
        projects = projects_result.scalars().all()
        
        user_dict = {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "display_name": user.display_name,
            "created_at": user.created_at,
            "project_count": len(projects),
            "projects": [
                {
                    "id": p.id,
                    "user_id": p.user_id,
                    "project_name": p.project_name,
                    "created_at": p.created_at
                }
                for p in projects
            ]
        }
        return user_dict
    
    async def get_all_with_projects(self, limit: int = 100) -> List[dict]:
        """Get all users with full project details"""
        # Get users
        users_result = await self.session.execute(
            select(User).limit(limit)
        )
        users = users_result.scalars().all()
        
        result = []
        for user in users:
            # Get projects for each user
            projects_result = await self.session.execute(
                select(UserProject).where(UserProject.user_id == user.id)
            )
            projects = projects_result.scalars().all()
            
            user_dict = {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "display_name": user.display_name,
                "created_at": user.created_at,
                "project_count": len(projects),
                "projects": [
                    {
                        "id": p.id,
                        "user_id": p.user_id,
                        "project_name": p.project_name,
                        "created_at": p.created_at
                    }
                    for p in projects
                ]
            }
            result.append(user_dict)
        
        return result

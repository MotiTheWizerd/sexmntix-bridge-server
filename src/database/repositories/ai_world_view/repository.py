"""
AI World View repository for database operations.
"""

from typing import Optional
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models.ai_world_view import AIWorldView
from src.database.repositories.base.repository import BaseRepository


class AIWorldViewRepository(BaseRepository[AIWorldView]):
    """
    Repository for AI World View database operations.

    Extends BaseRepository with world view-specific query methods.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(AIWorldView, session)

    async def get_by_user_project(
        self,
        user_id: str,
        project_id: str
    ) -> Optional[AIWorldView]:
        """
        Get world view for specific user/project combination.

        Args:
            user_id: User identifier (UUID)
            project_id: Project identifier (UUID)

        Returns:
            AIWorldView or None if not found
        """
        result = await self.session.execute(
            select(AIWorldView).where(
                and_(
                    AIWorldView.user_id == user_id,
                    AIWorldView.project_id == project_id
                )
            )
        )
        return result.scalar_one_or_none()

    async def create_or_update(
        self,
        user_id: str,
        project_id: str,
        core_beliefs: str
    ) -> AIWorldView:
        """
        Create or update world view for user/project.

        Args:
            user_id: User identifier (UUID)
            project_id: Project identifier (UUID)
            core_beliefs: Core beliefs summary text

        Returns:
            Created or updated AIWorldView instance
        """
        existing = await self.get_by_user_project(user_id, project_id)
        
        if existing:
            # Update existing
            existing.core_beliefs = core_beliefs
            from datetime import datetime
            existing.updated_at = datetime.utcnow()
            await self.session.flush()
            return existing
        else:
            # Create new
            world_view = AIWorldView(
                user_id=user_id,
                project_id=project_id,
                core_beliefs=core_beliefs
            )
            self.session.add(world_view)
            await self.session.flush()
            return world_view

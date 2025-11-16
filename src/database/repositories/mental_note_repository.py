from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from src.database.models import MentalNote
from .base_repository import BaseRepository
from typing import List, Optional


class MentalNoteRepository(BaseRepository[MentalNote]):
    def __init__(self, session: AsyncSession):
        super().__init__(MentalNote, session)

    async def get_by_session_id(self, session_id: str, limit: int = 100) -> List[MentalNote]:
        """Get mental notes by session ID.

        Args:
            session_id: Session identifier
            limit: Maximum number of notes to return

        Returns:
            List of mental notes for the session
        """
        result = await self.session.execute(
            select(MentalNote)
            .where(MentalNote.session_id == session_id)
            .order_by(desc(MentalNote.start_time))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_user_project(
        self,
        user_id: str,
        project_id: str,
        limit: int = 100
    ) -> List[MentalNote]:
        """Get mental notes by user and project.

        Args:
            user_id: User identifier
            project_id: Project identifier
            limit: Maximum number of notes to return

        Returns:
            List of mental notes for the user/project
        """
        result = await self.session.execute(
            select(MentalNote)
            .where(
                and_(
                    MentalNote.user_id == user_id,
                    MentalNote.project_id == project_id
                )
            )
            .order_by(desc(MentalNote.start_time))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_session_and_user(
        self,
        session_id: str,
        user_id: str,
        project_id: str,
        limit: int = 100
    ) -> List[MentalNote]:
        """Get mental notes by session ID and user/project.

        Args:
            session_id: Session identifier
            user_id: User identifier
            project_id: Project identifier
            limit: Maximum number of notes to return

        Returns:
            List of mental notes matching the criteria
        """
        result = await self.session.execute(
            select(MentalNote)
            .where(
                and_(
                    MentalNote.session_id == session_id,
                    MentalNote.user_id == user_id,
                    MentalNote.project_id == project_id
                )
            )
            .order_by(desc(MentalNote.start_time))
            .limit(limit)
        )
        return list(result.scalars().all())

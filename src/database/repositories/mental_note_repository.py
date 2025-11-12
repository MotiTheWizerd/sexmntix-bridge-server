from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from src.database.models import MentalNote
from .base_repository import BaseRepository
from typing import List


class MentalNoteRepository(BaseRepository[MentalNote]):
    def __init__(self, session: AsyncSession):
        super().__init__(MentalNote, session)

    async def get_by_session_id(self, session_id: str) -> List[MentalNote]:
        result = await self.session.execute(
            select(MentalNote)
            .where(MentalNote.session_id == session_id)
            .order_by(desc(MentalNote.start_time))
        )
        return list(result.scalars().all())

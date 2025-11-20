from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database.models import VscodeProject
from .base_repository import BaseRepository
from typing import List

class VscodeProjectRepository(BaseRepository[VscodeProject]):
    def __init__(self, session: AsyncSession):
        super().__init__(VscodeProject, session)

    async def get_by_user_id(self, user_id: str) -> List[VscodeProject]:
        result = await self.session.execute(
            select(VscodeProject).where(VscodeProject.user_id == user_id)
        )
        return list(result.scalars().all())

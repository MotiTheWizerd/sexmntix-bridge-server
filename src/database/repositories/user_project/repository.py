from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from src.database.models import UserProject
from ..base.base_repository import BaseRepository
from typing import List

class UserProjectRepository(BaseRepository[UserProject]):
    def __init__(self, session: AsyncSession):
        super().__init__(UserProject, session)

    async def get_by_user_id(self, user_id: str) -> List[UserProject]:
        result = await self.session.execute(
            select(UserProject).where(UserProject.user_id == user_id)
        )
        return list(result.scalars().all())

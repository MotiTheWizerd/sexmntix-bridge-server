from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from src.database.models import MemoryLog
from .base_repository import BaseRepository
from typing import List
from datetime import datetime


class MemoryLogRepository(BaseRepository[MemoryLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(MemoryLog, session)

    async def get_by_agent(self, agent: str, limit: int = 100) -> List[MemoryLog]:
        result = await self.session.execute(
            select(MemoryLog)
            .where(MemoryLog.agent == agent)
            .order_by(desc(MemoryLog.date))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_date_range(
        self, start_date: datetime, end_date: datetime, limit: int = 100
    ) -> List[MemoryLog]:
        result = await self.session.execute(
            select(MemoryLog)
            .where(MemoryLog.date.between(start_date, end_date))
            .order_by(desc(MemoryLog.date))
            .limit(limit)
        )
        return list(result.scalars().all())

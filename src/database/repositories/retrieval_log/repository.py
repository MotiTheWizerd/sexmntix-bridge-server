from datetime import datetime
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import RetrievalLog
from ..base.base_repository import BaseRepository


class RetrievalLogRepository(BaseRepository[RetrievalLog]):
    """
    Repository for retrieval logging.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(RetrievalLog, session)

    async def list_filtered(
        self,
        user_id: str | None = None,
        project_id: str | None = None,
        request_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[RetrievalLog]:
        conditions = []
        if user_id:
            conditions.append(RetrievalLog.user_id == user_id)
        if project_id:
            conditions.append(RetrievalLog.project_id == project_id)
        if request_id:
            conditions.append(RetrievalLog.request_id == request_id)
        if start_time:
            conditions.append(RetrievalLog.created_at >= start_time)
        if end_time:
            conditions.append(RetrievalLog.created_at <= end_time)

        stmt = select(RetrievalLog)
        if conditions:
            stmt = stmt.where(*conditions)
        stmt = stmt.order_by(RetrievalLog.created_at.desc()).offset(offset).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

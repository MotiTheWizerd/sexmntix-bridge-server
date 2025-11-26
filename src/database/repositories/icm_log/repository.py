from typing import List
from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import IcmLog
from ..base.base_repository import BaseRepository


class IcmLogRepository(BaseRepository[IcmLog]):
    """
    Repository for ICM logging.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(IcmLog, session)

    async def get_by_request(self, request_id: str) -> List[IcmLog]:
        result = await self.session.execute(select(IcmLog).where(IcmLog.request_id == request_id))
        return list(result.scalars().all())

    async def list_filtered(
        self,
        user_id: str | None = None,
        project_id: str | None = None,
        icm_type: str | None = None,
        request_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[IcmLog]:
        conditions = []
        if user_id:
            conditions.append(IcmLog.user_id == user_id)
        if project_id:
            conditions.append(IcmLog.project_id == project_id)
        if icm_type:
            conditions.append(IcmLog.icm_type == icm_type)
        if request_id:
            conditions.append(IcmLog.request_id == request_id)
        if start_time:
            conditions.append(IcmLog.created_at >= start_time)
        if end_time:
            conditions.append(IcmLog.created_at <= end_time)

        stmt = (
            select(IcmLog)
            .where(*conditions) if conditions else select(IcmLog)
        )
        stmt = stmt.order_by(IcmLog.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

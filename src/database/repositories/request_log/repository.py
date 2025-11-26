from datetime import datetime
from typing import List

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import RequestLog
from ..base.base_repository import BaseRepository


class RequestLogRepository(BaseRepository[RequestLog]):
    """
    Repository for request logging.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(RequestLog, session)

    async def list_filtered(
        self,
        path: str | None = None,
        method: str | None = None,
        user_id: str | None = None,
        project_id: str | None = None,
        request_id: str | None = None,
        start_time: datetime | None = None,
        end_time: datetime | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> List[RequestLog]:
        conditions = []
        if path:
            conditions.append(RequestLog.path == path)
        if method:
            conditions.append(RequestLog.method == method)
        if user_id:
            conditions.append(RequestLog.user_id == user_id)
        if project_id:
            conditions.append(RequestLog.project_id == project_id)
        if request_id:
            conditions.append(RequestLog.request_id == request_id)
        if start_time:
            conditions.append(RequestLog.created_at >= start_time)
        if end_time:
            conditions.append(RequestLog.created_at <= end_time)

        stmt = select(RequestLog)
        if conditions:
            stmt = stmt.where(*conditions)
        stmt = stmt.order_by(RequestLog.created_at.desc()).offset(offset).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies.database import get_db_session
from src.api.dependencies.logger import get_logger
from src.api.schemas.retrieval_log import RetrievalLogResponse
from src.database.repositories.retrieval_log import RetrievalLogRepository
from src.modules.core import Logger

router = APIRouter(prefix="/retrieval-logs", tags=["retrieval-logs"])


@router.get("", response_model=List[RetrievalLogResponse])
async def list_retrieval_logs(
    user_id: Optional[str] = None,
    project_id: Optional[str] = None,
    request_id: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
):
    """
    List retrieval logs with optional filters (user/project/request/time window).
    """
    repo = RetrievalLogRepository(db)
    logs = await repo.list_filtered(
        user_id=user_id,
        project_id=project_id,
        request_id=request_id,
        start_time=start_time,
        end_time=end_time,
        limit=limit,
        offset=offset,
    )
    if logger:
        logger.info(
            "[RETRIEVAL_LOGS] fetched",
            extra={
                "count": len(logs),
                "user_id": user_id,
                "project_id": project_id,
                "request_id": request_id,
                "start_time": start_time.isoformat() if start_time else None,
                "end_time": end_time.isoformat() if end_time else None,
                "limit": limit,
                "offset": offset,
            },
        )
    return logs


@router.get("/{id}", response_model=RetrievalLogResponse)
async def get_retrieval_log(
    id: str,
    db: AsyncSession = Depends(get_db_session),
    logger: Logger = Depends(get_logger),
):
    """
    Get a single retrieval log entry by ID.
    """
    repo = RetrievalLogRepository(db)
    log = await repo.get_by_id(id)
    if not log:
        raise HTTPException(status_code=404, detail="Retrieval log not found")
    if logger:
        logger.info("[RETRIEVAL_LOGS] fetched single", extra={"id": id})
    return log

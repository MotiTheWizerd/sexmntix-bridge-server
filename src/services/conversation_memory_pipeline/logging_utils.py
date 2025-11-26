from datetime import datetime
from typing import Any, Optional

from src.modules.core import Logger
from src.database.connection import DatabaseManager
from src.database.repositories.icm_log import IcmLogRepository
from src.database.repositories.retrieval_log import RetrievalLogRepository


async def log_session_icm(*, db_manager, logger, **kwargs):
    await log_icm(db_manager=db_manager, logger=logger, icm_type="session", **kwargs)


async def log_intent_icm(*, db_manager, logger, **kwargs):
    await log_icm(db_manager=db_manager, logger=logger, icm_type="intent", **kwargs)


async def log_time_icm(*, db_manager, logger, **kwargs):
    await log_icm(db_manager=db_manager, logger=logger, icm_type="time", **kwargs)


async def log_world_view_icm(*, db_manager, logger, **kwargs):
    await log_icm(db_manager=db_manager, logger=logger, icm_type="world_view", **kwargs)


async def log_identity_icm(*, db_manager, logger, **kwargs):
    await log_icm(db_manager=db_manager, logger=logger, icm_type="identity", **kwargs)


async def log_retrieval_icm(*, db_manager, logger, **kwargs):
    await log_icm(db_manager=db_manager, logger=logger, icm_type="retrieval", **kwargs)


async def log_icm(
    db_manager: Optional[DatabaseManager],
    logger: Optional[Logger],
    icm_type: str,
    request_id: str,
    query: Optional[str],
    user_id: Optional[str],
    project_id: Optional[str],
    session_id: Optional[str],
    retrieval_strategy: Optional[str],
    required_memory: Optional[Any],
    confidence: Optional[float],
    payload: Optional[Any],
    time_window_start: Optional[datetime] = None,
    time_window_end: Optional[datetime] = None,
    results_count: Optional[int] = None,
    limit: Optional[int] = None,
    min_similarity: Optional[float] = None,
) -> None:
    if not db_manager:
        return
    try:
        async with db_manager.session_factory() as session:
            repo = IcmLogRepository(session)
            await repo.create(
                request_id=request_id,
                icm_type=icm_type,
                query=query,
                user_id=user_id,
                project_id=project_id,
                session_id=session_id,
                retrieval_strategy=retrieval_strategy,
                required_memory=required_memory,
                time_window_start=time_window_start,
                time_window_end=time_window_end,
                confidence=confidence,
                payload=payload,
                results_count=results_count,
                limit=limit,
                min_similarity=min_similarity,
            )
    except Exception as e:
        if logger:
            logger.warning(
                "[FETCH_MEMORY_PIPELINE] failed to write icm log",
                extra={"error": str(e), "icm_type": icm_type, "request_id": request_id},
            )


async def log_retrieval_payload(
    db_manager: Optional[DatabaseManager],
    logger: Optional[Logger],
    request_id: str,
    query: Optional[str],
    user_id: Optional[str],
    project_id: Optional[str],
    session_id: Optional[str],
    required_memory: Optional[Any],
    results: Any,
    results_count: Optional[int],
    limit: Optional[int],
    min_similarity: Optional[float],
    target: Optional[str],
) -> None:
    if not db_manager:
        return
    try:
        async with db_manager.session_factory() as session:
            repo = RetrievalLogRepository(session)
            await repo.create(
                request_id=request_id,
                query=query,
                user_id=user_id,
                project_id=project_id,
                session_id=session_id,
                required_memory=required_memory,
                results=results,
                results_count=results_count,
                limit=limit,
                min_similarity=min_similarity,
                target=target,
            )
    except Exception as e:
        if logger:
            logger.warning(
                "[FETCH_MEMORY_PIPELINE] failed to write retrieval log",
                extra={"error": str(e), "request_id": request_id},
            )

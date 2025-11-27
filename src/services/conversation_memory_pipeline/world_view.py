from typing import Any, Dict, Optional
from src.modules.core import Logger
from src.database.connection import DatabaseManager
from src.database.repositories.icm_log.repository import IcmLogRepository
from src.modules.llm import LLMService
from src.services.world_view_service import WorldViewService


async def compute_world_view(
    db_manager: Optional[DatabaseManager],
    llm_service: Optional[LLMService],
    logger: Optional[Logger],
    user_id: Optional[str],
    project_id: Optional[str],
    session_id: Optional[str],
    summarize_with_llm: bool,
    reuse_cached: bool = True,
) -> Optional[Dict[str, Any]]:
    if not user_id or not project_id or not db_manager:
        return None
    try:
        if reuse_cached and session_id:
            cached = await _load_cached_world_view(
                db_manager=db_manager,
                user_id=user_id,
                project_id=project_id,
                session_id=session_id,
                logger=logger,
            )
            if cached:
                return cached

        service = WorldViewService(db_manager=db_manager, logger=logger, llm_service=llm_service)
        built = await service.build_world_view(
            user_id=user_id,
            project_id=project_id,
            session_id=session_id,
            summarize_with_llm=summarize_with_llm,
        )
        if isinstance(built, dict):
            built["is_cached"] = False
        return built
    except Exception as e:
        if logger:
            logger.warning(
                "[FETCH_MEMORY_PIPELINE] failed to compute world view",
                extra={"error": str(e), "user_id": user_id, "project_id": project_id},
            )
        return None


async def _load_cached_world_view(
    db_manager: DatabaseManager,
    user_id: str,
    project_id: str,
    session_id: str,
    logger: Optional[Logger],
) -> Optional[Dict[str, Any]]:
    try:
        async with db_manager.session_factory() as session:
            repo = IcmLogRepository(session)
            cached = await repo.get_latest_world_view(
                user_id=user_id,
                project_id=project_id,
                session_id=session_id,
            )
            if cached and isinstance(cached.payload, dict):
                payload = dict(cached.payload)
                payload["is_cached"] = True
                payload["cached_at"] = cached.created_at.isoformat() if cached.created_at else None
                return payload
    except Exception as e:
        if logger:
            logger.warning(
                "[FETCH_MEMORY_PIPELINE] failed to load cached world view",
                extra={"error": str(e), "session_id": session_id, "user_id": user_id, "project_id": project_id, "details": str(e)},
            )
    return None

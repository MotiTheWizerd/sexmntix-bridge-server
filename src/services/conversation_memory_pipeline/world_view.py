from typing import Any, Dict, Optional
from src.modules.core import Logger
from src.database.connection import DatabaseManager
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
) -> Optional[Dict[str, Any]]:
    if not user_id or not project_id or not db_manager:
        return None
    try:
        service = WorldViewService(db_manager=db_manager, logger=logger, llm_service=llm_service)
        return await service.build_world_view(
            user_id=user_id,
            project_id=project_id,
            session_id=session_id,
            summarize_with_llm=summarize_with_llm,
        )
    except Exception as e:
        if logger:
            logger.warning(
                "[FETCH_MEMORY_PIPELINE] failed to compute world view",
                extra={"error": str(e), "user_id": user_id, "project_id": project_id},
            )
        return None

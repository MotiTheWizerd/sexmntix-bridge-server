from fastapi import APIRouter, Depends, HTTPException, Request
from src.api.dependencies.logger import get_logger
from src.modules.core import Logger
from src.api.schemas.world_view import WorldViewResponse
from src.services.world_view_service import WorldViewService
from src.database.repositories.icm_log import IcmLogRepository
import uuid

router = APIRouter(prefix="/world-view", tags=["world-view"])


@router.get("", response_model=WorldViewResponse)
async def get_world_view(
    user_id: str,
    project_id: str,
    session_id: str | None = None,
    summarize_with_llm: bool = True,
    request: Request = None,
    logger: Logger = Depends(get_logger),
):
    """
    Build world view context (non-LLM) for a user/project/session.
    """
    if not user_id or not project_id:
        raise HTTPException(status_code=400, detail="user_id and project_id are required")

    request_id = str(uuid.uuid4())
    db_manager = request.app.state.db_manager
    llm_service = getattr(request.app.state, "llm_service", None)
    service = WorldViewService(db_manager=db_manager, logger=logger, llm_service=llm_service)
    payload = await service.build_world_view(
        user_id=user_id,
        project_id=project_id,
        session_id=session_id,
        summarize_with_llm=summarize_with_llm,
    )

    # Log to icm_logs as world_view
    try:
        async with db_manager.session_factory() as session:
            repo = IcmLogRepository(session)
            await repo.create(
                request_id=request_id,
                icm_type="world_view",
                query=None,
                user_id=user_id,
                project_id=project_id,
                session_id=session_id,
                retrieval_strategy=None,
                required_memory=None,
                confidence=None,
                payload=payload,
                results_count=None,
                limit=None,
                min_similarity=None,
            )
    except Exception as e:
        logger.warning("[WORLD_VIEW] failed to write icm log", extra={"error": str(e)})

    return payload

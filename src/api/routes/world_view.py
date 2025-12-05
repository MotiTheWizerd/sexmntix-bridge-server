from fastapi import APIRouter, Depends, HTTPException, Request
from src.api.dependencies.logger import get_logger
from src.modules.core import Logger

from src.api.schemas.world_view import WorldViewRequest, WorldViewResponse
from src.services.world_view_service import WorldViewService
from src.database.repositories.icm_log import IcmLogRepository
import uuid

router = APIRouter(prefix="/world-view", tags=["world-view"])


@router.post("", response_model=dict)
async def create_world_view(
    payload: WorldViewRequest,
    request: Request,
    logger: Logger = Depends(get_logger),
):
    """
    Create or update AI world view with core beliefs.
    
    Args:
        payload: World view creation request with user_id, project_id, and core_beliefs
    """
    if not payload.user_id or not payload.project_id:
        raise HTTPException(status_code=400, detail="user_id and project_id are required")
    
    if not payload.core_beliefs:
        raise HTTPException(status_code=400, detail="core_beliefs is required")
    
    db_manager = request.app.state.db_manager
    llm_service = getattr(request.app.state, "llm_service", None)
    
    service = WorldViewService(
        db_manager=db_manager,
        logger=logger,
        llm_service=llm_service
    )
    
    result = await service.create_world_view(
        user_id=payload.user_id,
        project_id=payload.project_id,
        core_beliefs=payload.core_beliefs
    )
    
    return result


@router.get("", response_model=WorldViewResponse)
async def get_world_view(
    user_id: str,
    project_id: str,
    session_id: str | None = None,
    summarize_with_llm: bool = True,
    provider: str | None = None,
    model: str | None = None,
    request: Request = None,
    logger: Logger = Depends(get_logger),
):
    """
    Build world view context for a user/project/session.
    
    Args:
        user_id: User identifier
        project_id: Project identifier
        session_id: Optional session identifier
        summarize_with_llm: Whether to use LLM for summarization
        provider: Optional LLM provider override (qwen, mistral, gemini)
        model: Optional model name override
    """
    if not user_id or not project_id:
        raise HTTPException(status_code=400, detail="user_id and project_id are required")

    request_id = str(uuid.uuid4())
    db_manager = request.app.state.db_manager
    llm_service = getattr(request.app.state, "llm_service", None)
    
    # Create world view service (compressor will be None, forcing LLM path)
    service = WorldViewService(
        db_manager=db_manager,
        logger=logger,
        llm_service=llm_service,
        compressor=None  # Don't use compressor, use LLM service instead
    )
    
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

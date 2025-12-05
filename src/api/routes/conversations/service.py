import uuid
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from src.api.formatters.conversation_formatter import ConversationFormatter
from src.api.schemas.conversation import ConversationCreate
from src.database.repositories import ConversationRepository
from src.database.repositories.request_log import RequestLogRepository
from src.database.repositories.request_log import RequestLogRepository
from src.modules.SXThalamus.prompts import SXThalamusPromptBuilder
from src.modules.SXPrefrontal import ICMBrain, TimeICMBrain, SXPrefrontalModel
from src.modules.core import Logger
from src.services.conversation_service import ConversationService
from src.services.conversation_memory_pipeline import ConversationMemoryPipeline
from src.services.conversation_memory_retrieval_service import ConversationMemoryRetrievalService
from .helpers import log_fetch_memory_state


class ConversationOrchestrator:
    """
    Orchestrates fetch-memory flow: request logging, pipeline, prompt, and LLM call.
    Keeps FastAPI routes thin.
    """

    def __init__(self, logger: Logger):
        self.logger = logger

    async def log_request(self, request_id: str, request, search_request) -> None:
        try:
            async with request.app.state.db_manager.session_factory() as session:
                repo = RequestLogRepository(session)
                await repo.create(
                    request_id=request_id,
                    path=str(request.url.path),
                    method=request.method,
                    user_id=search_request.user_id,
                    project_id=search_request.project_id,
                    session_id=search_request.session_id,
                    query_params=dict(request.query_params),
                    headers=dict(request.headers),
                    body=search_request.model_dump(),
                )
        except Exception as e:
            self.logger.warning("[REQUEST_LOG] failed to write request log", extra={"error": str(e)})

    async def fetch_memory(
        self,
        search_request,
        request,
    ) -> Dict[str, Any]:
        request_id = str(uuid.uuid4())
        await self.log_request(request_id, request, search_request)

        retrieval_service = ConversationMemoryRetrievalService(
            db_manager=request.app.state.db_manager,
            embedding_service=request.app.state.embedding_service,
            logger=self.logger,
        )
        llm_service = request.app.state.llm_service
        
        # Fetch user configuration for ICMs
        user_config_service = llm_service.user_config_service
        async with request.app.state.db_manager.session_factory() as session:
            user_config = await user_config_service.get_user_config(search_request.user_id, session)
        
        # Configure Intent ICM
        intent_config = user_config_service.get_icm_config(user_config, "intent_icm")
        intent_model = SXPrefrontalModel(
            provider=intent_config["provider"],
            model=intent_config["model"]
        )
        intent_icm = ICMBrain(model=intent_model)
        
        # Configure Time ICM
        time_config = user_config_service.get_icm_config(user_config, "time_icm")
        time_model = SXPrefrontalModel(
            provider=time_config["provider"],
            model=time_config["model"]
        )
        time_icm = TimeICMBrain(model=time_model, logger=self.logger)

        pipeline = ConversationMemoryPipeline(
            retrieval_service=retrieval_service,
            db_manager=request.app.state.db_manager,
            llm_service=llm_service,
            intent_icm=intent_icm,
            time_icm=time_icm,
            logger=self.logger,
        )

        pipeline_result = await pipeline.run(
            query=search_request.query,
            user_id=search_request.user_id,
            project_id=search_request.project_id,
            limit=search_request.limit,
            min_similarity=search_request.min_similarity,
            model=search_request.model,
            session_id=search_request.session_id,
            tz_offset_minutes=None,
        )

        results = pipeline_result.get("results", [])
        world_view = pipeline_result.get("world_view")
        inject_world_view = pipeline_result.get("inject_world_view", True)
        identity = pipeline_result.get("identity")

        if not results:
            return ConversationFormatter.format_memory_response("No relevant memories found.")

        llm_service = request.app.state.llm_service
        prompt_builder = SXThalamusPromptBuilder()
        prompt = prompt_builder.build_memory_synthesis_prompt(
            results,
            query=search_request.query,
            world_view=world_view,
            identity=identity,
            inject_full_world_view=inject_world_view,
        )

        log_fetch_memory_state(world_view, identity, results, prompt, inject_world_view)

        synthesized_memory = await llm_service.generate_content(
            prompt=prompt,
            user_id=search_request.user_id or "default",
            worker_type="memory_synthesizer",
        )

        return ConversationFormatter.format_memory_response(synthesized_memory)


def build_conversation_service(
    db_session,
    event_bus,
    logger: Logger,
) -> ConversationService:
    repo = ConversationRepository(db_session)
    return ConversationService(repository=repo, event_bus=event_bus, logger=logger)


def build_vector_search_service(
    vector_service,
    logger: Logger,
    db_session=None,
) -> ConversationService:
    repo = ConversationRepository(db_session) if db_session else None
    return ConversationService(vector_service=vector_service, repository=repo, logger=logger)

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.modules.SXPrefrontal import ICMBrain, TimeICMBrain
from src.modules.core import Logger
from src.database.connection import DatabaseManager
from src.database.repositories.icm_log import IcmLogRepository
from src.database.repositories.retrieval_log import RetrievalLogRepository
from src.database.repositories.conversation.repository import ConversationRepository
from src.services.conversation_memory_retrieval_service import ConversationMemoryRetrievalService
from src.services.world_view_service import WorldViewService
from src.services.identity_service import IdentityICMService

from .session_state import compute_session_state
from .world_view import compute_world_view
from .identity import compute_identity
from .logging_utils import log_icm, log_retrieval_payload


class ConversationMemoryPipeline:
    """
    Intent ICM -> Time ICM -> pgvector retrieval.
    """

    def __init__(
        self,
        retrieval_service: ConversationMemoryRetrievalService,
        db_manager: Optional[DatabaseManager] = None,
        llm_service: Optional[Any] = None,
        intent_icm: Optional[ICMBrain] = None,
        time_icm: Optional[TimeICMBrain] = None,
        logger: Optional[Logger] = None,
    ):
        self.retrieval_service = retrieval_service
        self.intent_icm = intent_icm or ICMBrain()
        self.time_icm = time_icm or TimeICMBrain()
        self.logger = logger
        self.db_manager = db_manager
        self.llm_service = llm_service
        self.identity_service = IdentityICMService(logger=logger)

    async def run(
        self,
        query: str,
        user_id: Optional[str],
        project_id: Optional[str],
        limit: int,
        min_similarity: float,
        model: Optional[str] = None,
        session_id: Optional[str] = None,
        tz_offset_minutes: Optional[int] = None,
        now: Optional[datetime] = None,
    ) -> Dict[str, Any]:
        now = now or datetime.now(timezone.utc)
        request_id = str(uuid.uuid4())
        sentinel_hit = False

        intent_result = self.intent_icm.classify(query)
        time_result = self.time_icm.resolve(
            query,
            now=now,
            tz_offset_minutes=tz_offset_minutes,
        )

        session_state = await compute_session_state(
            db_manager=self.db_manager,
            session_id=session_id,
            user_id=user_id,
            project_id=project_id,
            logger=self.logger,
        )

        start_time = _parse_iso(time_result.get("start_time"))
        end_time = _parse_iso(time_result.get("end_time"))

        retrieval_strategy = intent_result.get("retrieval_strategy", "none")
        required_memory = intent_result.get("required_memory", [])

        # If intent says none, switch to world_view to pull recent context
        if retrieval_strategy == "none":
            retrieval_strategy = "world_view"
        # If intent returned no required_memory, seed with query for logging
        if not required_memory:
            required_memory = [query]
        # If any required item contains the no-memory sentinel, treat as no retrieval
        if required_memory and any(_contains_no_memory_sentinel(item) for item in required_memory):
            sentinel_hit = True

        identity_payload = compute_identity(identity_service=self.identity_service, user_id=user_id, project_id=project_id, logger=self.logger)

        world_view_payload = await compute_world_view(
            db_manager=self.db_manager,
            llm_service=self.llm_service,
            logger=self.logger,
            user_id=user_id,
            project_id=project_id,
            session_id=session_id,
            summarize_with_llm=bool(not sentinel_hit and retrieval_strategy != "none"),
        )

        if self.logger:
            payload = {
                "intent": intent_result,
                "time": time_result,
                "user_id": user_id,
                "project_id": project_id,
                "start_time": start_time.isoformat() if start_time else None,
                "end_time": end_time.isoformat() if end_time else None,
                "limit": limit,
                "min_similarity": min_similarity,
                "query": query,
                "required_memory": required_memory,
                "retrieval_strategy": retrieval_strategy,
                "session_state": session_state,
                "world_view": world_view_payload,
                "identity": identity_payload,
            }
            self.logger.info(f"[FETCH_MEMORY_PIPELINE] intent/time resolution: {json.dumps(payload, default=str, ensure_ascii=False)}")

        if world_view_payload is not None:
            await log_icm(
                db_manager=self.db_manager,
                logger=self.logger,
                icm_type="world_view",
                request_id=request_id,
                query=query,
                user_id=user_id,
                project_id=project_id,
                session_id=session_id,
                retrieval_strategy=retrieval_strategy,
                required_memory=required_memory,
                confidence=None,
                payload=world_view_payload,
                limit=limit,
                min_similarity=min_similarity,
            )

        if identity_payload is not None:
            await log_icm(
                db_manager=self.db_manager,
                logger=self.logger,
                icm_type="identity",
                request_id=request_id,
                query=query,
                user_id=user_id,
                project_id=project_id,
                session_id=session_id,
                retrieval_strategy=retrieval_strategy,
                required_memory=required_memory,
                confidence=None,
                payload=identity_payload,
                limit=limit,
                min_similarity=min_similarity,
            )

        # Short-circuit if strategy is none OR sentinel indicates no memory retrieval should occur
        if retrieval_strategy == "none" or sentinel_hit:
            await log_icm(
                db_manager=self.db_manager,
                logger=self.logger,
                icm_type="session",
                request_id=request_id,
                query=query,
                user_id=user_id,
                project_id=project_id,
                session_id=session_id,
                retrieval_strategy=retrieval_strategy,
                required_memory=required_memory,
                confidence=None,
                payload=session_state,
                limit=limit,
                min_similarity=min_similarity,
            )
            await log_icm(
                db_manager=self.db_manager,
                logger=self.logger,
                icm_type="intent",
                request_id=request_id,
                query=query,
                user_id=user_id,
                project_id=project_id,
                session_id=session_id,
                retrieval_strategy=retrieval_strategy,
                required_memory=required_memory,
                confidence=intent_result.get("confidence"),
                payload={"intent": intent_result, "session_state": session_state},
                limit=limit,
                min_similarity=min_similarity,
            )
            await log_icm(
                db_manager=self.db_manager,
                logger=self.logger,
                icm_type="time",
                request_id=request_id,
                query=query,
                user_id=user_id,
                project_id=project_id,
                session_id=session_id,
                retrieval_strategy=retrieval_strategy,
                required_memory=required_memory,
                confidence=time_result.get("resolution_confidence"),
                payload=time_result,
                time_window_start=start_time,
                time_window_end=end_time,
                limit=limit,
                min_similarity=min_similarity,
            )
            await log_retrieval_payload(
                db_manager=self.db_manager,
                logger=self.logger,
                request_id=request_id,
                query=query,
                user_id=user_id,
                project_id=project_id,
                session_id=session_id,
                required_memory=required_memory,
                results=[],
                results_count=0,
                limit=limit,
                min_similarity=min_similarity,
                target="skipped",
            )
            return {
                "intent": intent_result,
                "time": time_result,
                "session": session_state,
                "identity": identity_payload,
                "world_view": world_view_payload,
                "results": [],
            }

        await log_icm(
            db_manager=self.db_manager,
            logger=self.logger,
            icm_type="session",
            request_id=request_id,
            query=query,
            user_id=user_id,
            project_id=project_id,
            session_id=session_id,
            retrieval_strategy=retrieval_strategy,
            required_memory=required_memory,
            confidence=None,
            payload=session_state,
            limit=limit,
            min_similarity=min_similarity,
        )

        await log_icm(
            db_manager=self.db_manager,
            logger=self.logger,
            icm_type="intent",
            request_id=request_id,
            query=query,
            user_id=user_id,
            project_id=project_id,
            session_id=session_id,
            retrieval_strategy=retrieval_strategy,
            required_memory=required_memory,
            confidence=intent_result.get("confidence"),
            payload={"intent": intent_result, "session_state": session_state},
            limit=limit,
            min_similarity=min_similarity,
        )

        await log_icm(
            db_manager=self.db_manager,
            logger=self.logger,
            icm_type="time",
            request_id=request_id,
            query=query,
            user_id=user_id,
            project_id=project_id,
            session_id=session_id,
            retrieval_strategy=retrieval_strategy,
            required_memory=required_memory,
            confidence=time_result.get("resolution_confidence"),
            payload=time_result,
            time_window_start=start_time,
            time_window_end=end_time,
            limit=limit,
            min_similarity=min_similarity,
        )

        if session_state is not None:
            await log_icm(
                db_manager=self.db_manager,
                logger=self.logger,
                icm_type="session",
                request_id=request_id,
                query=query,
                user_id=user_id,
                project_id=project_id,
                session_id=session_id,
                retrieval_strategy=retrieval_strategy,
                required_memory=required_memory,
                confidence=None,
                payload=session_state,
                limit=limit,
                min_similarity=min_similarity,
            )

        if retrieval_strategy == "none" or not required_memory:
            await log_retrieval_payload(
                db_manager=self.db_manager,
                logger=self.logger,
                request_id=request_id,
                query=query,
                user_id=user_id,
                project_id=project_id,
                session_id=session_id,
                required_memory=required_memory,
                results=[],
                results_count=0,
                limit=limit,
                min_similarity=min_similarity,
                target="skipped",
            )
            return {
                "intent": intent_result,
                "time": time_result,
                "session": session_state,
                "identity": identity_payload,
                "results": [],
            }

        results = await self.retrieval_service.fetch_required_memory(
            required_memory=required_memory,
            retrieval_strategy=retrieval_strategy,
            user_id=user_id,
            project_id=project_id,
            limit=limit,
            min_similarity=min_similarity,
            start_time=start_time,
            end_time=end_time,
            time_text=query,
            tz_offset_minutes=tz_offset_minutes,
            now=now,
        )

        if self.logger:
            result_payload = {
                "results_count": len(results),
                "start_time": start_time.isoformat() if start_time else None,
                "end_time": end_time.isoformat() if end_time else None,
                "min_similarity": min_similarity,
            }
            self.logger.info(f"[FETCH_MEMORY_PIPELINE] retrieval completed: {json.dumps(result_payload, default=str, ensure_ascii=False)}")

        await log_icm(
            db_manager=self.db_manager,
            logger=self.logger,
            icm_type="retrieval",
            request_id=request_id,
            query=query,
            user_id=user_id,
            project_id=project_id,
            session_id=session_id,
            retrieval_strategy=retrieval_strategy,
            required_memory=required_memory,
            confidence=None,
            payload={"intent": intent_result, "time": time_result},
            time_window_start=start_time,
            time_window_end=end_time,
            results_count=len(results),
            limit=limit,
            min_similarity=min_similarity,
        )

        await log_retrieval_payload(
            db_manager=self.db_manager,
            logger=self.logger,
            request_id=request_id,
            query=query,
            user_id=user_id,
            project_id=project_id,
            session_id=session_id,
            required_memory=required_memory,
            results=results,
            results_count=len(results),
            limit=limit,
            min_similarity=min_similarity,
            target="pgvector",
        )

        return {
            "intent": intent_result,
            "time": time_result,
            "session": session_state,
            "identity": identity_payload,
            "world_view": world_view_payload,
            "results": results,
        }


def _contains_no_memory_sentinel(text: Optional[str]) -> bool:
    if not text:
        return False
    return "[semantix-memory-block]" in text and "No relevant memories found" in text


def _parse_iso(value: Any) -> Optional[datetime]:
    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).replace(tzinfo=None)
    except Exception:
        return None

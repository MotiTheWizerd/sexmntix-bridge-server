"""
Pipeline to resolve intent + time and fetch conversation memory (pgvector).
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.modules.SXPrefrontal import ICMBrain, TimeICMBrain
from src.services.conversation_memory_retrieval_service import (
    ConversationMemoryRetrievalService,
)
from src.modules.core import Logger
from src.database.connection import DatabaseManager
from src.database.repositories.icm_log import IcmLogRepository
from src.database.repositories.retrieval_log import RetrievalLogRepository
from src.database.repositories.conversation.repository import ConversationRepository


class ConversationMemoryPipeline:
    """
    Intent ICM -> Time ICM -> pgvector retrieval.
    """

    def __init__(
        self,
        retrieval_service: ConversationMemoryRetrievalService,
        db_manager: Optional[DatabaseManager] = None,
        intent_icm: Optional[ICMBrain] = None,
        time_icm: Optional[TimeICMBrain] = None,
        logger: Optional[Logger] = None,
    ):
        self.retrieval_service = retrieval_service
        self.intent_icm = intent_icm or ICMBrain()
        self.time_icm = time_icm or TimeICMBrain()
        self.logger = logger
        self.db_manager = db_manager

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

        session_state = await self._compute_session_state(
            session_id=session_id,
            user_id=user_id,
            project_id=project_id,
        )

        start_time = self._parse_iso(time_result.get("start_time"))
        end_time = self._parse_iso(time_result.get("end_time"))

        retrieval_strategy = intent_result.get("retrieval_strategy", "none")
        required_memory = intent_result.get("required_memory", [])

        # If intent returned no required_memory, prefer a light no-retrieval exit instead of forced raw query
        if not required_memory:
            retrieval_strategy = "none"
        # If any required item contains the no-memory sentinel, treat as no retrieval
        if required_memory and any(self._contains_no_memory_sentinel(item) for item in required_memory):
            sentinel_hit = True

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
            }
            self.logger.info(f"[FETCH_MEMORY_PIPELINE] intent/time resolution: {json.dumps(payload, default=str, ensure_ascii=False)}")

        # Short-circuit if strategy is none OR sentinel indicates no memory retrieval should occur
        if retrieval_strategy == "none" or sentinel_hit:
            await self._log_icm(
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
            await self._log_icm(
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
            await self._log_icm(
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
            await self._log_retrieval_payload(
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
                "results": [],
            }

        await self._log_icm(
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

        await self._log_icm(
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

        await self._log_icm(
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
            await self._log_icm(
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
            await self._log_retrieval_payload(
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

        await self._log_icm(
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

        await self._log_retrieval_payload(
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
            "results": results,
        }

    async def _log_icm(
        self,
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
        if not self.db_manager:
            return
        try:
            async with self.db_manager.session_factory() as session:
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
            if self.logger:
                self.logger.warning(
                    "[FETCH_MEMORY_PIPELINE] failed to write icm log",
                    extra={"error": str(e), "icm_type": icm_type, "request_id": request_id},
                )

    async def _log_retrieval_payload(
        self,
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
        if not self.db_manager:
            return
        try:
            async with self.db_manager.session_factory() as session:
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
            if self.logger:
                self.logger.warning(
                    "[FETCH_MEMORY_PIPELINE] failed to write retrieval log",
                    extra={"error": str(e), "request_id": request_id},
                )

    async def _compute_session_state(
        self,
        session_id: Optional[str],
        user_id: Optional[str],
        project_id: Optional[str],
    ) -> Optional[Dict[str, Any]]:
        if not session_id or not self.db_manager:
            return None
        try:
            async with self.db_manager.session_factory() as session:
                repo = ConversationRepository(session)
                count = await repo.count_by_session(
                    session_id=session_id,
                    user_id=user_id,
                    project_id=project_id,
                )
                return {
                    "session_id": session_id,
                    "conversation_count": count,
                    "is_first_conversation": count <= 1,
                }
        except Exception as e:
            if self.logger:
                self.logger.warning(
                    "[FETCH_MEMORY_PIPELINE] failed to compute session state",
                    extra={"error": str(e), "session_id": session_id},
                )
            return None

    def _contains_no_memory_sentinel(self, text: Optional[str]) -> bool:
        if not text:
            return False
        return "[semantix-memory-block]" in text and "No relevant memories found" in text

    def _parse_iso(self, value: Any) -> Optional[datetime]:
        if not value or not isinstance(value, str):
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).replace(tzinfo=None)
        except Exception:
            return None

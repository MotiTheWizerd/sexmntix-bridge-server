"""
Pipeline to resolve intent + time and fetch conversation memory (pgvector).
"""

import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from src.modules.SXPrefrontal import ICMBrain, TimeICMBrain
from src.services.conversation_memory_retrieval_service import (
    ConversationMemoryRetrievalService,
)
from src.modules.core import Logger


class ConversationMemoryPipeline:
    """
    Intent ICM -> Time ICM -> pgvector retrieval.
    """

    def __init__(
        self,
        retrieval_service: ConversationMemoryRetrievalService,
        intent_icm: Optional[ICMBrain] = None,
        time_icm: Optional[TimeICMBrain] = None,
        logger: Optional[Logger] = None,
    ):
        self.retrieval_service = retrieval_service
        self.intent_icm = intent_icm or ICMBrain()
        self.time_icm = time_icm or TimeICMBrain()
        self.logger = logger

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

        intent_result = self.intent_icm.classify(query)
        time_result = self.time_icm.resolve(
            query,
            now=now,
            tz_offset_minutes=tz_offset_minutes,
        )

        start_time = self._parse_iso(time_result.get("start_time"))
        end_time = self._parse_iso(time_result.get("end_time"))

        retrieval_strategy = intent_result.get("retrieval_strategy", "none")
        required_memory = intent_result.get("required_memory", [])

        # Fallback: if intent returned no required_memory, use the raw query
        if not required_memory:
            required_memory = [query]
            if self.logger:
                self.logger.info(f"[FETCH_MEMORY_PIPELINE] using raw query as required_memory")

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
            }
            self.logger.info(f"[FETCH_MEMORY_PIPELINE] intent/time resolution: {json.dumps(payload, default=str, ensure_ascii=False)}")

        if retrieval_strategy == "none" or not required_memory:
            return {
                "intent": intent_result,
                "time": time_result,
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

        return {
            "intent": intent_result,
            "time": time_result,
            "results": results,
        }

    def _parse_iso(self, value: Any) -> Optional[datetime]:
        if not value or not isinstance(value, str):
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).replace(tzinfo=None)
        except Exception:
            return None

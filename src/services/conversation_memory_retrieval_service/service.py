import re
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone

from src.database.connection import DatabaseManager
from src.database.repositories.conversation.repository import ConversationRepository
from src.modules.embeddings import EmbeddingService
from src.modules.SXPrefrontal import TimeICMBrain
from src.modules.core import Logger

from .time_window import resolve_time_window, to_naive_utc
from .normalization import normalize_turns
from .search import fetch_world_view_recent, fetch_similar


class ConversationMemoryRetrievalService:
    """
    Retrieve required memory from conversations table (pgvector).
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        embedding_service: EmbeddingService,
        default_limit: int = 5,
        default_min_similarity: float = 0.7,
        time_icm: Optional[TimeICMBrain] = None,
        logger: Optional[Logger] = None,
    ):
        self.db_manager = db_manager
        self.embedding_service = embedding_service
        self.default_limit = default_limit
        self.default_min_similarity = default_min_similarity
        self.time_icm = time_icm or TimeICMBrain()
        self.logger = logger

    async def fetch_required_memory(
        self,
        required_memory: List[str],
        retrieval_strategy: str,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: Optional[int] = None,
        min_similarity: Optional[float] = None,
        start_time: Optional[Any] = None,
        end_time: Optional[Any] = None,
        time_text: Optional[str] = None,
        tz_offset_minutes: Optional[int] = None,
        now: Optional[datetime] = None,
    ) -> List[Dict[str, Any]]:
        """
        Fetch required memory items from conversations using pgvector.
        """
        if not required_memory or retrieval_strategy == "none":
            return []

        if retrieval_strategy not in {"conversations", "hybrid", "world_view"}:
            return []

        effective_limit = limit or self.default_limit
        effective_min_sim = (
            min_similarity if min_similarity is not None else self.default_min_similarity
        )

        time_result, start_time, end_time = resolve_time_window(
            self.time_icm,
            time_text,
            now=now or datetime.now(timezone.utc),
            tz_offset_minutes=tz_offset_minutes,
        ) if (start_time is None and end_time is None) else (None, to_naive_utc(start_time), to_naive_utc(end_time))

        # Normalize datetimes to naive UTC to match TIMESTAMP WITHOUT TIME ZONE schema
        start_time = to_naive_utc(start_time)
        end_time = to_naive_utc(end_time)

        async with self.db_manager.session_factory() as session:
            repo = ConversationRepository(session)

            # World-view strategy: recent conversations, no embedding search
            if retrieval_strategy == "world_view":
                return await fetch_world_view_recent(
                    repo=repo,
                    user_id=user_id,
                    project_id=project_id,
                    limit=effective_limit,
                )

            # First: time window only fetch for observability and hard gating
            if start_time and end_time:
                time_window_matches = await repo.get_by_time_range(
                    start_time=start_time,
                    end_time=end_time,
                    user_id=user_id,
                    project_id=project_id,
                    limit=effective_limit,
                )
                if self.logger:
                    self.logger.info(
                        "[FETCH_MEMORY_TIMESLICE] resolved window",
                        extra={
                            "start_time": start_time.isoformat(),
                            "end_time": end_time.isoformat(),
                            "matches": len(time_window_matches),
                            "user_id": user_id,
                            "project_id": project_id,
                        },
                    )
                if not time_window_matches:
                    return []

            results: List[Dict[str, Any]] = []

            for item in required_memory:
                embedding_result = await self.embedding_service.generate_embedding(item)
                query_embedding = embedding_result.embedding

                matches: List[Tuple[Any, float]] = await fetch_similar(
                    repo=repo,
                    query_embedding=query_embedding,
                    start_time=start_time,
                    end_time=end_time,
                    user_id=user_id,
                    project_id=project_id,
                    limit=effective_limit,
                    min_similarity=effective_min_sim,
                )

                # Debug logging
                try:
                    print(
                        f"[FETCH_MEMORY_DEBUG] item='{item}', "
                        f"matches={len(matches)}, "
                        f"user_id={user_id}, project_id={project_id}, "
                        f"start_time={start_time}, end_time={end_time}, "
                        f"min_similarity={effective_min_sim}"
                    )
                    for idx, (conv, sim) in enumerate(matches[:3]):
                        print(
                            f"[FETCH_MEMORY_DEBUG] top{idx+1} conv_id={conv.id}, "
                            f"created_at={conv.created_at}, similarity={sim}"
                        )
                except Exception:
                    pass

                for conv, similarity in matches:
                    turns = normalize_turns(conv)
                    results.append(
                        {
                            "source": "conversations",
                            "similarity": similarity,
                            "conversation_id": conv.conversation_id,
                            "created_at": conv.created_at.isoformat() if conv.created_at else None,
                            "model": conv.model,
                            "project_id": conv.project_id,
                            "user_id": conv.user_id,
                            "turns": turns,
                            "topic": conv.raw_data.get("topic") if conv.raw_data else None,
                            "required_item": item,
                        }
                    )

        # Optional: sort across items by similarity descending
        results.sort(key=lambda r: r.get("similarity", 0), reverse=True)
        return results

import re
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone

from src.database.connection import DatabaseManager
from src.database.repositories.conversation.repository import ConversationRepository
from src.modules.embeddings import EmbeddingService
from src.modules.SXPrefrontal import TimeICMBrain
from src.modules.core import Logger


class ConversationMemoryRetrievalService:
    """
    Retrieve required memory from conversations table (pgvector).
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        embedding_service: EmbeddingService,
        default_limit: int = 5,
        default_min_similarity: float = 0.5,
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

        # Resolve time window if not provided but time_text is given
        if (start_time is None and end_time is None) and time_text and self.time_icm:
            time_result = self.time_icm.resolve(
                time_text,
                now=now or datetime.now(timezone.utc),
                tz_offset_minutes=tz_offset_minutes,
            )
            start_time = self._parse_iso(time_result.get("start_time"))
            end_time = self._parse_iso(time_result.get("end_time"))
            # Simple logging
            print(
                f"[TIME_ICM] time_text='{time_text}', "
                f"start_time={time_result.get('start_time')}, "
                f"end_time={time_result.get('end_time')}, "
                f"confidence={time_result.get('resolution_confidence')}"
            )

        # Normalize datetimes to naive UTC to match TIMESTAMP WITHOUT TIME ZONE schema
        start_time = self._to_naive_utc(start_time)
        end_time = self._to_naive_utc(end_time)

        async with self.db_manager.session_factory() as session:
            repo = ConversationRepository(session)

            # World-view strategy: recent conversations, no embedding search
            if retrieval_strategy == "world_view":
                recent = await repo.get_recent_by_user_project(
                    user_id=user_id,
                    project_id=project_id,
                    limit=effective_limit,
                )
                results = []
                for conv in recent:
                    turns = self._normalize_turns(conv)
                    results.append(
                        {
                            "source": "world_view",
                            "similarity": 1.0,
                            "conversation_id": conv.conversation_id,
                            "created_at": conv.created_at.isoformat() if conv.created_at else None,
                            "model": conv.model,
                            "project_id": conv.project_id,
                            "user_id": conv.user_id,
                            "turns": turns,
                            "topic": conv.raw_data.get("topic") if conv.raw_data else None,
                            "required_item": "world_view",
                        }
                    )
                return results

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

                # Prefer time-bounded search when window is supplied
                if start_time and end_time:
                    matches: List[Tuple[Any, float]] = await repo.search_similar_by_time_range(
                        query_embedding=query_embedding,
                        start_time=start_time,
                        end_time=end_time,
                        user_id=user_id,
                        project_id=project_id,
                        limit=effective_limit,
                        min_similarity=effective_min_sim,
                        distance_metric="cosine",
                    )
                else:
                    matches: List[Tuple[Any, float]] = await repo.search_similar(
                        query_embedding=query_embedding,
                        user_id=user_id,
                        project_id=project_id,
                        limit=effective_limit,
                        min_similarity=effective_min_sim,
                        distance_metric="cosine",
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
                    turns = self._normalize_turns(conv)
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

    def _parse_iso(self, value: Any) -> Optional[datetime]:
        if not value or not isinstance(value, str):
            return None
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except Exception:
            return None

    def _to_naive_utc(self, dt: Optional[datetime]) -> Optional[datetime]:
        """
        Convert an aware datetime to naive UTC (tzinfo stripped) to match TIMESTAMP WITHOUT TIME ZONE.
        """
        if dt is None:
            return None
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
        return dt

    def _normalize_turns(self, conv: Any) -> List[Dict[str, Any]]:
        """
        Normalize conversation raw_data into user/assistant turn objects with metadata.

        Shape:
        {
          "user": "...",
          "assistant": "...",
          "metadata": {
            "timestamp": "...",
            "conversation_id": "...",
            "source": "conversation"
          }
        }
        """
        raw = conv.raw_data or {}
        candidates = []

        if isinstance(raw, list):
            candidates = raw
        elif isinstance(raw, dict):
            if isinstance(raw.get("conversation"), list):
                candidates = raw["conversation"]
            elif isinstance(raw.get("messages"), list):
                candidates = raw["messages"]
            elif isinstance(raw.get("memory_log"), dict):
                mem_log = raw["memory_log"]
                if isinstance(mem_log.get("conversation"), list):
                    candidates = mem_log["conversation"]

        turns: List[Dict[str, Any]] = []
        pending_user: Optional[str] = None

        for msg in candidates:
            if not isinstance(msg, dict):
                continue

            role = msg.get("role", "").strip()
            text = self._extract_text(msg).strip()
            if not role or not text:
                continue

            timestamp = (
                msg.get("timestamp")
                or msg.get("created_at")
                or (conv.created_at.isoformat() if conv.created_at else None)
            )

            metadata = {
                "timestamp": timestamp,
                "conversation_id": conv.conversation_id,
                "source": "conversation",
            }

            if role == "user":
                pending_user = text
            elif role == "assistant":
                if pending_user is not None:
                    turns.append(
                        {"user": pending_user, "assistant": text, "metadata": metadata}
                    )
                    pending_user = None
                else:
                    turns.append({"user": "", "assistant": text, "metadata": metadata})

        if pending_user:
            turns.append(
                {
                    "user": pending_user,
                    "assistant": "",
                    "metadata": {
                        "timestamp": conv.created_at.isoformat() if conv.created_at else None,
                        "conversation_id": conv.conversation_id,
                        "source": "conversation",
                    },
                }
            )

        return turns

    def _extract_text(self, msg: Dict[str, Any]) -> str:
        """
        Extract text content from various message shapes.
        """
        if not isinstance(msg, dict):
            return ""
        text = ""
        if msg.get("text"):
            text = str(msg.get("text", ""))
        elif isinstance(msg.get("content"), str):
            text = msg["content"]
        elif isinstance(msg.get("content"), list):
            parts = msg["content"]
            text = " ".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in parts
            )
        elif isinstance(msg.get("parts"), list):
            text = " ".join(
                part.get("text", "") if isinstance(part, dict) else str(part)
                for part in msg["parts"]
            )
        return self._strip_memory_blocks(text)

    def _strip_memory_blocks(self, text: str) -> str:
        """
        Remove [semantix-memory-block] ... [semantix-end-memory-block] content before use.
        """
        if not text:
            return ""
        return re.sub(
            r"\[semantix-memory-block\].*?\[semantix-end-memory-block\]",
            "",
            text,
            flags=re.IGNORECASE | re.DOTALL,
        ).strip()

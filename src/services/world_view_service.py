from datetime import datetime
from typing import Any, Dict, Optional, List
import re

from sqlalchemy import select, desc

from src.database.connection import DatabaseManager
from src.database.repositories.conversation.repository import ConversationRepository
from src.modules.core import Logger
from src.modules.SXPrefrontal import CompressionBrain
from src.modules.llm import LLMService


class WorldViewService:
    """
    Non-LLM world view aggregator. Builds a compact context payload from DB state.
    """

    def __init__(
        self,
        db_manager: DatabaseManager,
        logger: Optional[Logger] = None,
        compressor: Optional[CompressionBrain] = None,
        llm_service: Optional[LLMService] = None,
    ):
        self.db_manager = db_manager
        self.logger = logger
        self.compressor = compressor or CompressionBrain()
        self.llm_service = llm_service

    async def build_world_view(
        self,
        user_id: str,
        project_id: str,
        session_id: Optional[str] = None,
        recent_limit: int = 5,
        summarize_with_llm: bool = False,
    ) -> Dict[str, Any]:
        conversation_count = 0
        recent_conversations: List[Dict[str, Any]] = []
        short_term_memory: Optional[str] = None

        async with self.db_manager.session_factory() as session:
            conv_repo = ConversationRepository(session)

            if session_id:
                conversation_count = await conv_repo.count_by_session(
                    session_id=session_id,
                    user_id=user_id,
                    project_id=project_id,
                )
            else:
                conversation_count = await conv_repo.count_by_user_project(
                    user_id=user_id,
                    project_id=project_id,
                )

            # Recent conversations for user/project
            conv_rows = await session.execute(
                select(conv_repo.model)
                .where(
                    conv_repo.model.user_id == user_id,
                    conv_repo.model.project_id == project_id,
                )
                .order_by(desc(conv_repo.model.created_at))
                .limit(recent_limit)
            )
            for conv in conv_rows.scalars().all():
                snippet = ""
                summary = ""
                first_text = ""
                last_text = ""
                if conv.raw_data and isinstance(conv.raw_data, dict):
                    convo_list = conv.raw_data.get("conversation") or conv.raw_data.get("messages") or []
                    if isinstance(convo_list, list) and convo_list:
                        first = convo_list[0] if len(convo_list) > 0 else {}
                        last = convo_list[-1] if len(convo_list) > 0 else {}
                        def extract_text(item: Any) -> str:
                            if not isinstance(item, dict):
                                return ""
                            return str(item.get("text") or item.get("content") or "")
                        first_text = self._strip_memory_blocks(extract_text(first))
                        last_text = self._strip_memory_blocks(extract_text(last))
                        snippet = first_text[:200]
                        summary = f"user: {first_text[:120]} ... assistant: {last_text[:120]}"
                recent_conversations.append(
                    {
                        "id": conv.id,
                        "conversation_id": conv.conversation_id,
                        "session_id": conv.session_id,
                        "model": conv.model,
                        "created_at": conv.created_at.isoformat() if conv.created_at else None,
                        "snippet": snippet,
                        "summary": summary,
                        "first_text": first_text,
                        "last_text": last_text,
                    }
                )

        if summarize_with_llm and recent_conversations:
            if self.llm_service:
                try:
                    prompt = self._build_llm_prompt(recent_conversations)
                    short_term_memory = await self.llm_service.generate_content(
                        prompt=prompt,
                        user_id=user_id,
                        worker_type="world_view_summarizer",
                    )
                except Exception as e:
                    short_term_memory = None
                    if self.logger:
                        self.logger.warning("[WORLD_VIEW] LLM summary failed", extra={"error": str(e), "user_id": user_id, "project_id": project_id})
            elif self.compressor:
                try:
                    short_term_memory = self._compress_conversations(recent_conversations)
                except Exception as e:
                    short_term_memory = None
                    if self.logger:
                        self.logger.warning("[WORLD_VIEW] compression failed", extra={"error": str(e), "user_id": user_id, "project_id": project_id})

        payload = {
            "user_id": user_id,
            "project_id": project_id,
            "session_id": session_id,
            "conversation_count": conversation_count,
            "is_first_conversation": conversation_count <= 1 if session_id else None,
            "recent_conversations": recent_conversations,
            "recent_memory_logs": [],
            "recent_mental_notes": [],
            "short_term_memory": short_term_memory,
            "is_cached": False,
            "generated_at": datetime.utcnow().isoformat(),
        }

        if self.logger:
            self.logger.info(
                "[WORLD_VIEW] built",
                extra={
                    "user_id": user_id,
                    "project_id": project_id,
                    "session_id": session_id,
                    "conversation_count": conversation_count,
                    "recent_conversations": len(recent_conversations),
                    "summarized": summarize_with_llm and bool(payload.get("short_term_memory")),
                },
            )

        return payload

    def _compress_conversations(self, conversations: List[Dict[str, Any]]) -> str:
        units = []
        for conv in conversations[:10]:
            user_text = self._strip_memory_blocks(conv.get("first_text", "") or "")
            assistant_text = self._strip_memory_blocks(conv.get("last_text", "") or "")
            compressed = self.compressor.compress(user_text=user_text, assistant_text=assistant_text)
            unit = compressed.get("semantic_unit", "").strip()
            if unit:
                units.append(unit)
        # Clean up payload (remove first/last text from exposed data)
        for conv in conversations:
            conv.pop("first_text", None)
            conv.pop("last_text", None)
        return "\n".join(f"- {u}" for u in units if u)

    def _build_llm_prompt(self, conversations: List[Dict[str, Any]]) -> str:
        lines = []
        for idx, conv in enumerate(conversations[:3], start=1):
            summary = self._strip_memory_blocks(conv.get("summary") or conv.get("snippet") or "")
            created_at = conv.get("created_at") or ""
            lines.append(f"{idx}. ({created_at}) {summary}")
        joined = "\n".join(lines)
        return (
            "Summarize these recent conversations into a concise short-term memory (under 120 words). "
            "Focus on key intents, decisions, and context. Return plain text, no bullets needed.\n"
            f"{joined}"
        )

    def _strip_memory_blocks(self, text: str) -> str:
        if not text:
            return ""
        return re.sub(r"\[semantix-memory-block\].*?\[semantix-end-memory-block\]", "", text, flags=re.DOTALL).strip()

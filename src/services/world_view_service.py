from datetime import datetime
from typing import Any, Dict, Optional, List
import re

from sqlalchemy import select, desc

from src.database.connection import DatabaseManager
from src.database.repositories.conversation.repository import ConversationRepository
from src.database.repositories.ai_world_view.repository import AIWorldViewRepository
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

        # Build conversation summary (incremental approach)
        conversation_summary = None
        if summarize_with_llm and recent_conversations:
            if self.logger:
                self.logger.info(
                    f"[WORLD_VIEW] Building conversation summary for {len(recent_conversations)} conversations",
                    extra={"has_compressor": bool(self.compressor), "has_llm_service": bool(self.llm_service)}
                )
            conversation_summary = await self._build_conversation_summary(
                recent_conversations=recent_conversations,
                user_id=user_id,
                project_id=project_id,
                session_id=session_id,
            )
            if self.logger:
                self.logger.info(
                    f"[WORLD_VIEW] Summary generated: {bool(conversation_summary)}, length: {len(conversation_summary) if conversation_summary else 0}"
                )



        payload = {
            "user_id": user_id,
            "project_id": project_id,
            "session_id": session_id,
            "conversation_count": conversation_count,
            "is_first_conversation": conversation_count <= 1 if session_id else None,
            "conversation_summary": conversation_summary,
            "recent_conversations": [],  # Deprecated, kept for backward compatibility
            "recent_memory_logs": [],
            "recent_mental_notes": [],
            "short_term_memory": conversation_summary,  # Alias for backward compatibility
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

    async def create_world_view(
        self,
        user_id: str,
        project_id: str,
        core_beliefs: str
    ) -> Dict[str, Any]:
        """
        Create or update AI world view with core beliefs.

        Args:
            user_id: User identifier (UUID)
            project_id: Project identifier (UUID)
            core_beliefs: Summary of core beliefs about identity

        Returns:
            Dictionary with world view data
        """
        async with self.db_manager.session_factory() as session:
            world_view_repo = AIWorldViewRepository(session)
            
            world_view = await world_view_repo.create_or_update(
                user_id=user_id,
                project_id=project_id,
                core_beliefs=core_beliefs
            )
            
            await session.commit()
            
            if self.logger:
                self.logger.info(
                    f"[WORLD_VIEW] Created/updated world view for user {user_id}, project {project_id}"
                )
            
            return {
                "id": world_view.id,
                "user_id": world_view.user_id,
                "project_id": world_view.project_id,
                "core_beliefs": world_view.core_beliefs,
                "created_at": world_view.created_at.isoformat(),
                "updated_at": world_view.updated_at.isoformat()
            }

    async def get_world_view(
        self,
        user_id: str,
        project_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get AI world view for user/project.

        Args:
            user_id: User identifier (UUID)
            project_id: Project identifier (UUID)

        Returns:
            Dictionary with world view data or None if not found
        """
        async with self.db_manager.session_factory() as session:
            world_view_repo = AIWorldViewRepository(session)
            
            world_view = await world_view_repo.get_by_user_project(
                user_id=user_id,
                project_id=project_id
            )
            
            if not world_view:
                return None
            
            return {
                "id": world_view.id,
                "user_id": world_view.user_id,
                "project_id": world_view.project_id,
                "core_beliefs": world_view.core_beliefs,
                "created_at": world_view.created_at.isoformat(),
                "updated_at": world_view.updated_at.isoformat()
            }

    async def _build_conversation_summary(
        self,
        recent_conversations: List[Dict[str, Any]],
        user_id: str,
        project_id: str,
        session_id: Optional[str],
    ) -> Optional[str]:
        """
        Build incremental conversation summary.
        
        Loads cached summary if available, then only summarizes new conversations.
        """
        if self.logger:
            self.logger.info(f"[WORLD_VIEW] _build_conversation_summary called with {len(recent_conversations)} conversations")
        try:
            # Try to load cached summary from previous world view
            cached_summary = None
            last_summary_timestamp = None
            
            if session_id and self.db_manager:
                async with self.db_manager.session_factory() as session:
                    from src.database.repositories.icm_log import IcmLogRepository
                    repo = IcmLogRepository(session)
                    cached_world_view = await repo.get_latest_world_view(
                        user_id=user_id,
                        project_id=project_id,
                        session_id=session_id,
                    )
                    if cached_world_view and isinstance(cached_world_view.payload, dict):
                        cached_summary = cached_world_view.payload.get("conversation_summary")
                        last_summary_timestamp = cached_world_view.created_at
            
            # Identify new conversations since last summary
            new_conversations = []
            if last_summary_timestamp and cached_summary:  # Only filter if we have both timestamp AND summary
                for conv in recent_conversations:
                    conv_time_str = conv.get("created_at")
                    if conv_time_str:
                        try:
                            from datetime import datetime
                            conv_time = datetime.fromisoformat(conv_time_str.replace('Z', '+00:00'))
                            if conv_time > last_summary_timestamp:
                                new_conversations.append(conv)
                        except:
                            new_conversations.append(conv)  # Include if parsing fails
                    else:
                        new_conversations.append(conv)
            else:
                # No cache or no summary, summarize all
                new_conversations = recent_conversations
            
            if not new_conversations:
                # No new conversations, return cached summary
                return cached_summary
            
            # Generate summary for new conversations
            # Use LLM service if available, otherwise fall back to compressor
            if self.logger:
                self.logger.info(
                    f"[WORLD_VIEW] Generating summary for {len(new_conversations)} new conversations. "
                    f"Has compressor: {bool(self.compressor)}, Has LLM service: {bool(self.llm_service)}"
                )
            new_summary = None
            if self.llm_service:
                if self.logger:
                    self.logger.info("[WORLD_VIEW] Using LLM service for summary")
                prompt = self._build_incremental_summary_prompt(new_conversations, cached_summary)
                new_summary = await self.llm_service.generate_content(
                    prompt=prompt,
                    user_id=user_id,
                    worker_type="world_view_summarizer",
                )
            elif self.compressor:
                if self.logger:
                    self.logger.info("[WORLD_VIEW] Using compressor for summary")
                new_summary = self._compress_conversations_incremental(new_conversations, cached_summary)
            
            if self.logger:
                self.logger.info(f"[WORLD_VIEW] Summary generated: {bool(new_summary)}")
            
            return new_summary
            
        except Exception as e:
            if self.logger:
                self.logger.warning(
                    "[WORLD_VIEW] Failed to build conversation summary",
                    extra={"error": str(e), "error_type": type(e).__name__, "user_id": user_id, "project_id": project_id},
                    exc_info=True
                )
            return None

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

    def _build_incremental_summary_prompt(
        self,
        new_conversations: List[Dict[str, Any]],
        cached_summary: Optional[str]
    ) -> str:
        """Build prompt for incremental summary generation."""
        lines = []
        for idx, conv in enumerate(new_conversations, start=1):
            first_text = self._strip_memory_blocks(conv.get("first_text", "") or "")
            last_text = self._strip_memory_blocks(conv.get("last_text", "") or "")
            created_at = conv.get("created_at") or ""
            summary = f"User: {first_text[:100]}... | Assistant: {last_text[:100]}..."
            lines.append(f"{idx}. ({created_at}) {summary}")
        
        joined = "\n".join(lines)
        
        if cached_summary:
            return (
                f"You have an existing conversation summary:\n\n{cached_summary}\n\n"
                "Now append these new conversations to the summary. "
                "Continue the numbered list from where it left off. "
                "Format: step number, timestamp, brief description (1-2 sentences). "
                "Focus on: what was discussed, decisions made, actions taken.\n\n"
                f"New conversations:\n{joined}\n\n"
                "Return ONLY the complete updated summary (including previous steps + new steps)."
            )
        else:
            return (
                "Create a chronological step-by-step summary of these conversations. "
                "Format as numbered list with timestamps. "
                "Focus on: what was discussed, decisions made, actions taken. "
                "Keep each step concise (1-2 sentences).\n\n"
                f"Conversations:\n{joined}\n\n"
                "Return the summary:"
            )

    def _compress_conversations_incremental(
        self,
        new_conversations: List[Dict[str, Any]],
        cached_summary: Optional[str]
    ) -> str:
        """Compress new conversations and append to cached summary."""
        if self.logger:
            self.logger.info(f"[WORLD_VIEW] _compress_conversations_incremental called with {len(new_conversations)} conversations, cached_summary exists: {bool(cached_summary)}")
        
        units = []
        start_num = 1
        
        if cached_summary:
            lines = cached_summary.strip().split("\n")
            for line in reversed(lines):
                if line.strip() and line[0].isdigit():
                    try:
                        num = int(line.split(".")[0])
                        start_num = num + 1
                        break
                    except:
                        pass
        
        for idx, conv in enumerate(new_conversations, start=start_num):
            user_text = self._strip_memory_blocks(conv.get("first_text", "") or "")
            assistant_text = self._strip_memory_blocks(conv.get("last_text", "") or "")
            created_at = conv.get("created_at") or ""
            
            if self.logger:
                self.logger.info(f"[WORLD_VIEW] Compressing conversation {idx}: user_text_len={len(user_text)}, assistant_text_len={len(assistant_text)}")
            
            try:
                compressed = self.compressor.compress(user_text=user_text, assistant_text=assistant_text)
                unit = compressed.get("semantic_unit", "").strip()
                if self.logger:
                    self.logger.info(f"[WORLD_VIEW] Compressed result: {unit[:100] if unit else 'EMPTY'}")
                if unit:
                    units.append(f"{idx}. ({created_at}) {unit}")
            except Exception as e:
                if self.logger:
                    self.logger.error(f"[WORLD_VIEW] Compression failed for conversation {idx}: {e}")
        
        result = ""
        if cached_summary:
            result = cached_summary + "\n" + "\n".join(units)
        else:
            result = "\n".join(units)
        
        if self.logger:
            self.logger.info(f"[WORLD_VIEW] Final compressed summary length: {len(result)}, units generated: {len(units)}")
        
        return result

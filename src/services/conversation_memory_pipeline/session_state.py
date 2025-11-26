from typing import Any, Dict, Optional
from src.modules.core import Logger
from src.database.connection import DatabaseManager
from src.database.repositories.conversation.repository import ConversationRepository


async def compute_session_state(
    db_manager: Optional[DatabaseManager],
    session_id: Optional[str],
    user_id: Optional[str],
    project_id: Optional[str],
    logger: Optional[Logger],
) -> Optional[Dict[str, Any]]:
    if not session_id or not db_manager:
        return None
    try:
        async with db_manager.session_factory() as session:
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
        if logger:
            logger.warning(
                "[FETCH_MEMORY_PIPELINE] failed to compute session state",
                extra={"error": str(e), "session_id": session_id},
            )
        return None

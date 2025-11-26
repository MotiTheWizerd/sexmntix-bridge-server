from typing import Any, Dict, List, Tuple

from src.database.repositories.conversation.repository import ConversationRepository
from .normalization import normalize_turns


async def fetch_world_view_recent(repo: ConversationRepository, user_id: str, project_id: str, limit: int) -> List[Dict[str, Any]]:
    recent = await repo.get_recent_by_user_project(
        user_id=user_id,
        project_id=project_id,
        limit=limit,
    )
    results = []
    for conv in recent:
        turns = normalize_turns(conv)
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


async def fetch_similar(
    repo: ConversationRepository,
    query_embedding,
    start_time,
    end_time,
    user_id,
    project_id,
    limit,
    min_similarity,
) -> List[Tuple[Any, float]]:
    if start_time and end_time:
        return await repo.search_similar_by_time_range(
            query_embedding=query_embedding,
            start_time=start_time,
            end_time=end_time,
            user_id=user_id,
            project_id=project_id,
            limit=limit,
            min_similarity=min_similarity,
            distance_metric="cosine",
        )
    return await repo.search_similar(
        query_embedding=query_embedding,
        user_id=user_id,
        project_id=project_id,
        limit=limit,
        min_similarity=min_similarity,
        distance_metric="cosine",
    )

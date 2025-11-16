"""
Conversation repository for database operations.

Provides CRUD operations and semantic search for conversations.
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from src.database.models import Conversation
from .base_repository import BaseRepository
from typing import List, Tuple, Optional


class ConversationRepository(BaseRepository[Conversation]):
    """
    Repository for Conversation database operations.

    Extends BaseRepository with conversation-specific query methods.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(Conversation, session)

    async def get_by_conversation_id(self, conversation_id: str) -> Optional[Conversation]:
        """
        Get conversation by unique conversation_id.

        Args:
            conversation_id: Unique conversation identifier (UUID)

        Returns:
            Conversation or None if not found
        """
        result = await self.session.execute(
            select(Conversation).where(Conversation.conversation_id == conversation_id)
        )
        return result.scalar_one_or_none()

    async def get_by_model(self, model: str, limit: int = 100) -> List[Conversation]:
        """
        Get conversations by AI model.

        Args:
            model: AI model name (e.g., "gpt-5-1-instant")
            limit: Maximum number of results

        Returns:
            List of conversations for the specified model
        """
        result = await self.session.execute(
            select(Conversation)
            .where(Conversation.model == model)
            .order_by(desc(Conversation.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_user_project(
        self,
        user_id: str,
        project_id: str,
        limit: int = 100
    ) -> List[Conversation]:
        """
        Get conversations for specific user/project combination.

        Args:
            user_id: User identifier
            project_id: Project identifier
            limit: Maximum number of results

        Returns:
            List of conversations for the user/project
        """
        result = await self.session.execute(
            select(Conversation)
            .where(
                and_(
                    Conversation.user_id == user_id,
                    Conversation.project_id == project_id
                )
            )
            .order_by(desc(Conversation.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def search_similar(
        self,
        query_embedding: List[float],
        user_id: Optional[str] = None,
        project_id: Optional[str] = None,
        limit: int = 10,
        min_similarity: float = 0.0,
        distance_metric: str = "cosine"
    ) -> List[Tuple[Conversation, float]]:
        """
        Perform semantic similarity search using pgvector.

        Args:
            query_embedding: The embedding vector to search for (768 dimensions)
            user_id: Filter by user_id (optional)
            project_id: Filter by project_id (optional)
            limit: Maximum number of results to return
            min_similarity: Minimum similarity threshold (0.0 to 1.0)
            distance_metric: Distance metric to use ('cosine', 'l2', or 'inner_product')

        Returns:
            List of tuples: (Conversation, similarity_score)
            similarity_score is between 0.0 and 1.0 (higher = more similar)
        """
        # Build where conditions
        conditions = [Conversation.embedding.is_not(None)]
        if user_id:
            conditions.append(Conversation.user_id == user_id)
        if project_id:
            conditions.append(Conversation.project_id == project_id)

        # Select distance operator based on metric
        if distance_metric == "cosine":
            # Cosine distance: 0 = identical, 2 = opposite
            # Convert to similarity: 1 - (distance / 2) gives 0-1 range
            distance_expr = Conversation.embedding.cosine_distance(query_embedding)
            similarity_expr = (1 - (distance_expr / 2)).label('similarity')
        elif distance_metric == "l2":
            # L2 distance: 0 = identical, unbounded
            # Convert to similarity using exponential decay
            distance_expr = Conversation.embedding.l2_distance(query_embedding)
            similarity_expr = (1 / (1 + distance_expr)).label('similarity')
        elif distance_metric == "inner_product":
            # Inner product (negative distance for max heap behavior)
            # Higher inner product = more similar
            distance_expr = Conversation.embedding.max_inner_product(query_embedding)
            similarity_expr = distance_expr.label('similarity')
        else:
            raise ValueError(f"Unknown distance metric: {distance_metric}")

        # Execute query
        result = await self.session.execute(
            select(Conversation, similarity_expr)
            .where(and_(*conditions))
            .order_by(distance_expr)  # Order by distance (ascending = most similar first)
            .limit(limit)
        )

        # Filter by minimum similarity and return
        rows = result.all()
        return [
            (row.Conversation, row.similarity)
            for row in rows
            if row.similarity >= min_similarity
        ]

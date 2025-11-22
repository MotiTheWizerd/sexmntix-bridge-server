from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from src.database.models import MemoryLog
from .base_repository import BaseRepository
from typing import List, Tuple, Optional
from datetime import datetime


class MemoryLogRepository(BaseRepository[MemoryLog]):
    def __init__(self, session: AsyncSession):
        super().__init__(MemoryLog, session)

    async def get_by_agent(self, agent: str, limit: int = 100) -> List[MemoryLog]:
        result = await self.session.execute(
            select(MemoryLog)
            .where(MemoryLog.agent == agent)
            .order_by(desc(MemoryLog.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_date_range(
        self, start_date: datetime, end_date: datetime, limit: int = 100
    ) -> List[MemoryLog]:
        result = await self.session.execute(
            select(MemoryLog)
            .where(MemoryLog.created_at.between(start_date, end_date))
            .order_by(desc(MemoryLog.created_at))
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
    ) -> List[Tuple[MemoryLog, float]]:
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
            List of tuples: (MemoryLog, similarity_score)
            similarity_score is between 0.0 and 1.0 (higher = more similar)
        """
        # Build where conditions
        conditions = [MemoryLog.embedding.is_not(None)]
        if user_id:
            conditions.append(MemoryLog.user_id == user_id)
        if project_id:
            conditions.append(MemoryLog.project_id == project_id)

        # Select distance operator based on metric
        if distance_metric == "cosine":
            # Cosine distance: 0 = identical, 2 = opposite
            # Convert to similarity: 1 - (distance / 2) gives 0-1 range
            distance_expr = MemoryLog.embedding.cosine_distance(query_embedding)
            similarity_expr = (1 - (distance_expr / 2)).label('similarity')
        elif distance_metric == "l2":
            # L2 distance: 0 = identical, unbounded
            # Convert to similarity using exponential decay
            distance_expr = MemoryLog.embedding.l2_distance(query_embedding)
            similarity_expr = (1 / (1 + distance_expr)).label('similarity')
        elif distance_metric == "inner_product":
            # Inner product (negative distance for max heap behavior)
            # Higher inner product = more similar
            distance_expr = MemoryLog.embedding.max_inner_product(query_embedding)
            similarity_expr = distance_expr.label('similarity')
        else:
            raise ValueError(f"Unknown distance metric: {distance_metric}")

        # Execute query
        result = await self.session.execute(
            select(MemoryLog, similarity_expr)
            .where(and_(*conditions))
            .order_by(distance_expr)  # Order by distance (ascending = most similar first)
            .limit(limit)
        )

        # Filter by minimum similarity and return
        rows = result.all()
        return [
            (row.MemoryLog, row.similarity)
            for row in rows
            if row.similarity >= min_similarity
        ]

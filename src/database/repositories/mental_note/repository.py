from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, and_
from src.database.models import MentalNote
from ..base.base_repository import BaseRepository
from typing import List, Optional


class MentalNoteRepository(BaseRepository[MentalNote]):
    def __init__(self, session: AsyncSession):
        super().__init__(MentalNote, session)

    async def get_by_session_id(self, session_id: str, limit: int = 100) -> List[MentalNote]:
        """Get mental notes by session ID.

        Args:
            session_id: Session identifier
            limit: Maximum number of notes to return

        Returns:
            List of mental notes for the session
        """
        result = await self.session.execute(
            select(MentalNote)
            .where(MentalNote.session_id == session_id)
            .order_by(desc(MentalNote.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_user_project(
        self,
        user_id: str,
        project_id: str,
        limit: int = 100
    ) -> List[MentalNote]:
        """Get mental notes by user and project.

        Args:
            user_id: User identifier
            project_id: Project identifier
            limit: Maximum number of notes to return

        Returns:
            List of mental notes for the user/project
        """
        result = await self.session.execute(
            select(MentalNote)
            .where(
                and_(
                    MentalNote.user_id == user_id,
                    MentalNote.project_id == project_id
                )
            )
            .order_by(desc(MentalNote.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_session_and_user(
        self,
        session_id: str,
        user_id: str,
        project_id: str,
        limit: int = 100
    ) -> List[MentalNote]:
        """Get mental notes by session ID and user/project.

        Args:
            session_id: Session identifier
            user_id: User identifier
            project_id: Project identifier
            limit: Maximum number of notes to return

        Returns:
            List of mental notes matching the criteria
        """
        result = await self.session.execute(
            select(MentalNote)
            .where(
                and_(
                    MentalNote.session_id == session_id,
                    MentalNote.user_id == user_id,
                    MentalNote.project_id == project_id
                )
            )
            .order_by(desc(MentalNote.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_without_embeddings(self, limit: int = 100) -> List[MentalNote]:
        """Get mental notes that don't have embeddings yet.

        Args:
            limit: Maximum number of notes to return

        Returns:
            List of mental notes where embedding IS NULL
        """
        result = await self.session.execute(
            select(MentalNote)
            .where(MentalNote.embedding.is_(None))
            .order_by(desc(MentalNote.created_at))
            .limit(limit)
        )
        return list(result.scalars().all())

    async def search_similar(
        self,
        query_embedding: List[float],
        user_id: str,
        project_id: str,
        limit: int = 10,
        min_similarity: float = 0.0
    ) -> List[tuple[MentalNote, float]]:
        """
        Perform semantic similarity search using pgvector.

        Args:
            query_embedding: The embedding vector to search for (768 dimensions)
            user_id: Filter by user_id
            project_id: Filter by project_id
            limit: Maximum number of results to return
            min_similarity: Minimum similarity threshold (0.0 to 1.0)

        Returns:
            List of tuples: (MentalNote, similarity_score)
            similarity_score is between 0.0 and 1.0 (higher = more similar)
        """
        # Build where conditions
        conditions = [
            MentalNote.embedding.is_not(None),
            MentalNote.user_id == user_id,
            MentalNote.project_id == project_id
        ]

        # Cosine distance: 0 = identical, 2 = opposite
        # Convert to similarity: 1 - (distance / 2) gives 0-1 range
        distance_expr = MentalNote.embedding.cosine_distance(query_embedding)
        similarity_expr = (1 - (distance_expr / 2)).label('similarity')

        # Execute query
        result = await self.session.execute(
            select(MentalNote, similarity_expr)
            .where(and_(*conditions))
            .order_by(distance_expr)  # Order by distance (ascending = most similar first)
            .limit(limit)
        )

        # Filter by minimum similarity and return
        rows = result.all()
        return [
            (row.MentalNote, row.similarity)
            for row in rows
            if row.similarity >= min_similarity
        ]

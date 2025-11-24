"""
Dependency injection for mental note routes.
"""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.api.dependencies.database import get_db_session
from src.database.repositories import MentalNoteRepository


def get_mental_note_repository(
    db: AsyncSession = Depends(get_db_session)
) -> MentalNoteRepository:
    """
    Get mental note repository instance.

    Args:
        db: Database session

    Returns:
        MentalNoteRepository instance
    """
    return MentalNoteRepository(db)

from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import Example
from .base_repository import BaseRepository


class ExampleRepository(BaseRepository[Example]):
    def __init__(self, session: AsyncSession):
        super().__init__(Example, session)

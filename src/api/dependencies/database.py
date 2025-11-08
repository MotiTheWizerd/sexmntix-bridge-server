from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession
from typing import AsyncGenerator


async def get_db_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    db_manager = request.app.state.db_manager
    async for session in db_manager.get_session():
        yield session

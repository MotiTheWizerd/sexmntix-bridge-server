import asyncio
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
from src.database import DatabaseManager
from src.database.repositories.conversation_repository import ConversationRepository
from src.api.bootstrap.config import load_app_config

async def check():
    load_dotenv()
    config = load_app_config()
    db = DatabaseManager(config.database_url)

    async with db.session_factory() as session:
        repo = ConversationRepository(session)
        count = await repo.count_without_embeddings()
        print(f'Conversations without embeddings: {count}')

    await db.close()

asyncio.run(check())

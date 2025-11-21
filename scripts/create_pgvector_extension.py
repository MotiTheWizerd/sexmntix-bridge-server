"""Create pgvector extension in PostgreSQL"""
import asyncio
from dotenv import load_dotenv
from sqlalchemy import text as sql_text
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.database import DatabaseManager
from src.api.bootstrap.config import load_app_config

async def main():
    load_dotenv()
    app_config = load_app_config()
    db = DatabaseManager(app_config.database_url)

    async with db.session_factory() as session:
        await session.execute(sql_text('CREATE EXTENSION IF NOT EXISTS vector'))
        await session.commit()
        print('✓ pgvector extension created successfully')

    await db.close()

if __name__ == "__main__":
    asyncio.run(main())

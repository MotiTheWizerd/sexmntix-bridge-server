"""
Test script to verify session_id column was added to conversations table.
"""
import asyncio
from sqlalchemy import inspect
from src.database.session import engine


async def check_schema():
    """Check if session_id column exists in conversations table."""
    async with engine.begin() as conn:
        result = await conn.run_sync(
            lambda sync_conn: inspect(sync_conn).get_columns('conversations')
        )

        print('\nConversations table columns:')
        for col in result:
            print(f"  - {col['name']}: {col['type']}")

        # Check if session_id exists
        session_id_exists = any(col['name'] == 'session_id' for col in result)

        if session_id_exists:
            print("\n✅ SUCCESS: session_id column found in conversations table!")
        else:
            print("\n❌ ERROR: session_id column NOT found in conversations table!")

        return session_id_exists


if __name__ == "__main__":
    success = asyncio.run(check_schema())
    exit(0 if success else 1)

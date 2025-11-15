"""
Script to migrate memory JSON files from .semantix/memories/delta/ to PostgreSQL database.

This script reads all memory JSON files from the delta folder and imports them
into the memory_logs table in the database.
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path to import from src
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select
from src.database.models import MemoryLog


async def load_memory_files(delta_path: Path) -> List[Dict[str, Any]]:
    """Load all JSON memory files from the delta folder."""
    memories = []

    if not delta_path.exists():
        print(f"Error: Delta path does not exist: {delta_path}")
        return memories

    json_files = list(delta_path.glob("*.json"))
    print(f"Found {len(json_files)} JSON files in {delta_path}")

    for json_file in json_files:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                memories.append({
                    'filename': json_file.name,
                    'data': data
                })
                print(f"  [OK] Loaded: {json_file.name}")
        except Exception as e:
            print(f"  [ERROR] Error loading {json_file.name}: {e}")

    return memories


async def parse_date(date_str: str) -> datetime:
    """Parse date string from memory JSON to datetime object."""
    try:
        # Try parsing YYYY-MM-DD format
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        # If that fails, try ISO format
        try:
            return datetime.fromisoformat(date_str)
        except ValueError:
            # Default to current date if parsing fails
            print(f"  Warning: Could not parse date '{date_str}', using current date")
            return datetime.utcnow()


async def memory_exists(session: AsyncSession, task: str, date: datetime) -> bool:
    """Check if a memory with the same task and date already exists."""
    result = await session.execute(
        select(MemoryLog).where(
            MemoryLog.task == task,
            MemoryLog.date == date
        )
    )
    return result.scalar_one_or_none() is not None


async def import_memories(session: AsyncSession, memories: List[Dict[str, Any]]) -> Dict[str, int]:
    """Import memories into the database."""
    stats = {
        'total': len(memories),
        'imported': 0,
        'skipped': 0,
        'errors': 0
    }

    for memory in memories:
        filename = memory['filename']
        data = memory['data']

        try:
            # Extract required fields
            task = data.get('task', 'unknown')
            agent = data.get('agent', 'unknown')
            date_str = data.get('date', datetime.utcnow().strftime("%Y-%m-%d"))
            date = await parse_date(date_str)

            # Check if already exists
            if await memory_exists(session, task, date):
                print(f"  [SKIP] Skipped (already exists): {filename}")
                stats['skipped'] += 1
                continue

            # Create MemoryLog instance
            memory_log = MemoryLog(
                task=task,
                agent=agent,
                date=date,
                raw_data=data,  # Store entire JSON as JSONB
                user_id=None,  # Can be set if you have a default user
                project_id="default",  # Default project
                created_at=datetime.utcnow()
            )

            session.add(memory_log)
            print(f"  [OK] Imported: {filename} (task: {task}, date: {date_str})")
            stats['imported'] += 1

        except Exception as e:
            print(f"  [ERROR] Error importing {filename}: {e}")
            stats['errors'] += 1

    # Commit all changes
    try:
        await session.commit()
        print(f"\n[OK] Successfully committed {stats['imported']} memories to database")
    except Exception as e:
        await session.rollback()
        print(f"\n[ERROR] Error committing to database: {e}")
        raise

    return stats


async def main():
    """Main migration function."""
    print("=" * 80)
    print("Memory Migration Script - Delta Folder to PostgreSQL")
    print("=" * 80)
    print()

    # Get project root and delta path
    project_root = Path(__file__).parent.parent
    delta_path = project_root / ".semantix" / "memories" / "delta"

    print(f"Project root: {project_root}")
    print(f"Delta path: {delta_path}")
    print()

    # Load memory files
    print("Loading memory files...")
    memories = await load_memory_files(delta_path)

    if not memories:
        print("No memories to import. Exiting.")
        return

    print()
    print(f"Loaded {len(memories)} memory files")
    print()

    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        print("Error: DATABASE_URL not set in environment")
        return

    print(f"Database: {database_url.split('@')[1] if '@' in database_url else database_url}")
    print()

    # Create async engine and session
    engine = create_async_engine(database_url, echo=False)
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    # Import memories
    print("Importing memories...")
    async with async_session() as session:
        stats = await import_memories(session, memories)

    await engine.dispose()

    # Print summary
    print()
    print("=" * 80)
    print("Migration Summary")
    print("=" * 80)
    print(f"Total files processed: {stats['total']}")
    print(f"Successfully imported: {stats['imported']}")
    print(f"Skipped (duplicates):  {stats['skipped']}")
    print(f"Errors:                {stats['errors']}")
    print("=" * 80)

    if stats['errors'] > 0:
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())

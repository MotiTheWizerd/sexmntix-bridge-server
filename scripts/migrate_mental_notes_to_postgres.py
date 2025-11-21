"""
Simple migration script: Import mental notes from temp/ directory to PostgreSQL.

Reads mental notes JSON files, adds user_id/project_id, and inserts into mental_notes table.

Usage:
    python scripts/migrate_mental_notes_to_postgres.py --dry-run  # Preview without writing
    python scripts/migrate_mental_notes_to_postgres.py            # Actually migrate
"""

import argparse
import asyncio
import json
import sys
import uuid
from pathlib import Path
from typing import Dict, Any

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        return None

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

# Ensure project root is on path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.api.bootstrap.config import load_app_config
from src.database import DatabaseManager
from src.database.repositories.mental_note_repository import MentalNoteRepository


# Default values
DEFAULT_USER_ID = "84e17260-ff03-409b-bf30-0b5ba52a2ab4"
DEFAULT_PROJECT_ID = "84e17260-ff03-409b-bf30-0b5ba52a2ab4"

# Namespace for generating deterministic UUIDs from sessionId strings
SESSION_UUID_NAMESPACE = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8')


def generate_session_uuid(session_id_str: str) -> str:
    """
    Generate a deterministic UUID from a sessionId string.
    Same sessionId always produces the same UUID.

    Args:
        session_id_str: The original sessionId (e.g., "2025-10-04-17-03")

    Returns:
        UUID string that will be consistent for the same sessionId
    """
    return str(uuid.uuid5(SESSION_UUID_NAMESPACE, session_id_str))


def parse_args():
    parser = argparse.ArgumentParser(description="Migrate mental notes from temp/ to PostgreSQL")
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("temp"),
        help="Source directory containing mental notes JSON files (default: temp/)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview migration without writing to database"
    )
    parser.add_argument(
        "--user-id",
        default=DEFAULT_USER_ID,
        help=f"User ID for all mental notes (default: {DEFAULT_USER_ID})"
    )
    parser.add_argument(
        "--project-id",
        default=DEFAULT_PROJECT_ID,
        help=f"Project ID for all mental notes (default: {DEFAULT_PROJECT_ID})"
    )
    return parser.parse_args()


def validate_mental_note(data: Dict[str, Any]) -> tuple[bool, str]:
    """Validate mental note structure."""

    # Check for required fields
    if "startTime" not in data:
        return False, "Missing 'startTime' field"

    if not isinstance(data["startTime"], int):
        return False, f"'startTime' must be integer, got {type(data['startTime']).__name__}"

    # Check for entries array (optional but common)
    if "entries" in data and not isinstance(data["entries"], list):
        return False, "'entries' must be a list"

    return True, "Valid"


async def migrate_files(source_dir: Path, dry_run: bool, user_id: str, project_id: str):
    """Migrate all mental notes JSON files from source directory to PostgreSQL."""

    # Find all JSON files
    json_files = sorted(source_dir.glob("*.json"))

    if not json_files:
        print(f"No JSON files found in {source_dir}")
        return

    print(f"Found {len(json_files)} JSON files")
    print(f"Mode: {'DRY RUN (no changes will be made)' if dry_run else 'LIVE (will insert into database)'}")
    print(f"Target: user_id={user_id}, project_id={project_id}")
    print("-" * 80)

    if dry_run:
        # Dry run - just validate files
        success_count = 0
        error_count = 0

        for json_file in json_files:
            try:
                with json_file.open("r", encoding="utf-8") as f:
                    raw_json = json.load(f)

                # Validate structure
                is_valid, message = validate_mental_note(raw_json)

                if not is_valid:
                    print(f"✗ {json_file.name} - Validation Error: {message}")
                    error_count += 1
                    continue

                # Extract info for display
                session_id_str = raw_json.get("sessionId", "unknown")
                start_time = raw_json.get("startTime", 0)
                entries_count = len(raw_json.get("entries", []))

                print(f"✓ {json_file.name}")
                print(f"  Session: {session_id_str}")
                print(f"  Start Time: {start_time}")
                print(f"  Entries: {entries_count}")
                success_count += 1

            except json.JSONDecodeError as e:
                print(f"✗ {json_file.name} - JSON Error: {e}")
                error_count += 1
            except Exception as e:
                print(f"✗ {json_file.name} - Error: {e}")
                error_count += 1

        print("-" * 80)
        print(f"Dry run complete: {success_count} valid, {error_count} errors")
        if error_count == 0:
            print("\nAll files valid! Run without --dry-run to migrate.")

    else:
        # Live migration
        load_dotenv()
        app_config = load_app_config()
        db_manager = DatabaseManager(app_config.database_url)

        success_count = 0
        error_count = 0

        async with db_manager.session_factory() as session:
            repo = MentalNoteRepository(session)

            for json_file in json_files:
                try:
                    with json_file.open("r", encoding="utf-8") as f:
                        raw_json = json.load(f)

                    # Validate structure
                    is_valid, message = validate_mental_note(raw_json)

                    if not is_valid:
                        print(f"✗ {json_file.name} - Validation Error: {message}")
                        error_count += 1
                        continue

                    # Extract required fields
                    start_time = raw_json["startTime"]

                    # Generate deterministic UUID from sessionId string
                    # Same sessionId always gets the same UUID
                    session_id_str = raw_json.get("sessionId", "unknown-session")
                    session_id = generate_session_uuid(session_id_str)

                    # Build raw_data (preserve entire original structure)
                    raw_data = dict(raw_json)

                    # Insert into database
                    mental_note = await repo.create(
                        session_id=session_id,
                        start_time=start_time,
                        raw_data=raw_data,
                        user_id=user_id,
                        project_id=project_id
                    )

                    original_session_str = raw_json.get("sessionId", "unknown")
                    print(f"✓ {json_file.name}")
                    print(f"  Original session: {original_session_str}")
                    print(f"  Session UUID: {session_id}")
                    print(f"  Mental note ID: {mental_note.id}")
                    success_count += 1

                except json.JSONDecodeError as e:
                    print(f"✗ {json_file.name} - JSON Error: {e}")
                    error_count += 1
                except Exception as e:
                    print(f"✗ {json_file.name} - Error: {e}")
                    error_count += 1

            # Commit all at once
            await session.commit()

        await db_manager.close()

        print("-" * 80)
        print(f"Migration complete: {success_count} inserted, {error_count} errors")


def main():
    args = parse_args()

    if not args.source.exists():
        print(f"Error: Source directory '{args.source}' does not exist")
        sys.exit(1)

    asyncio.run(migrate_files(
        source_dir=args.source,
        dry_run=args.dry_run,
        user_id=args.user_id,
        project_id=args.project_id
    ))


if __name__ == "__main__":
    main()

"""
Simple migration script: Import memory logs from temp/ directory to PostgreSQL.

Reads JSON files from temp/, wraps them in the required format, and inserts into memory_logs table.
Fields not in the MemoryLogData schema are automatically dropped.

Usage:
    python scripts/migrate_temp_to_postgres.py --dry-run  # Preview without writing
    python scripts/migrate_temp_to_postgres.py            # Actually migrate
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        return None

# Ensure project root is on path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.api.bootstrap.config import load_app_config
from src.api.schemas.memory_log import MemoryLogCreate, MemoryLogData
from src.database import DatabaseManager
from src.database.repositories.memory_log_repository import MemoryLogRepository
from pydantic import ValidationError


# Default values
DEFAULT_USER_ID = "84e17260-ff03-409b-bf30-0b5ba52a2ab4"
DEFAULT_PROJECT_ID = "semntix-code"
DEFAULT_SESSION_ID = "temp-migration"


def parse_args():
    parser = argparse.ArgumentParser(description="Migrate memory logs from temp/ to PostgreSQL")
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("temp"),
        help="Source directory containing JSON files (default: temp/)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview migration without writing to database"
    )
    parser.add_argument(
        "--user-id",
        default=DEFAULT_USER_ID,
        help=f"User ID for all memory logs (default: {DEFAULT_USER_ID})"
    )
    parser.add_argument(
        "--project-id",
        default=DEFAULT_PROJECT_ID,
        help=f"Project ID for all memory logs (default: {DEFAULT_PROJECT_ID})"
    )
    parser.add_argument(
        "--session-id",
        default=DEFAULT_SESSION_ID,
        help=f"Session ID for all memory logs (default: {DEFAULT_SESSION_ID})"
    )
    return parser.parse_args()


def ensure_datetime(date_str: str) -> datetime:
    """Convert date string to datetime object."""
    # Try YYYY-MM-DD format first
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        pass

    # Try ISO format
    try:
        return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
    except ValueError:
        pass

    # Fallback to current time
    print(f"Warning: Could not parse date '{date_str}', using current time")
    return datetime.utcnow()


def sanitize_memory_log(memory_log: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitize memory log fields to match schema constraints.
    Drops or fixes fields that don't match schema validation.
    """
    # Make a copy to avoid modifying original
    memory_log = dict(memory_log)

    # Ensure required fields have defaults if missing
    if "agent" not in memory_log or not memory_log["agent"]:
        memory_log["agent"] = "unknown"
    if "date" not in memory_log or not memory_log["date"]:
        memory_log["date"] = datetime.utcnow().strftime("%Y-%m-%d")

    # Fix task field - use 'id' if 'task' is missing
    if "task" not in memory_log or not memory_log["task"]:
        if "id" in memory_log and memory_log["id"]:
            memory_log["task"] = memory_log["id"]
        else:
            memory_log["task"] = "unknown-task"

    # Fix outcomes fields if present
    if "outcomes" in memory_log and isinstance(memory_log["outcomes"], dict):
        outcomes = memory_log["outcomes"]

        # Fix technical_debt_reduced - drop if not valid
        if "technical_debt_reduced" in outcomes:
            value = outcomes["technical_debt_reduced"]
            if value not in ["low", "medium", "high"]:
                outcomes.pop("technical_debt_reduced")

        # Fix follow_up_needed - must be boolean
        if "follow_up_needed" in outcomes:
            value = outcomes["follow_up_needed"]
            if not isinstance(value, bool):
                # Try to convert string to boolean or drop it
                if isinstance(value, str):
                    value_lower = value.lower().strip()
                    if value_lower in ["true", "yes", "1"]:
                        outcomes["follow_up_needed"] = True
                    elif value_lower in ["false", "no", "0"]:
                        outcomes["follow_up_needed"] = False
                    else:
                        # Can't convert - drop it
                        outcomes.pop("follow_up_needed")
                else:
                    outcomes.pop("follow_up_needed")

    # Fix files_modified - must be string or int, not dict/list
    if "files_modified" in memory_log:
        value = memory_log["files_modified"]
        if isinstance(value, (dict, list)):
            # If it's a list, convert to count
            if isinstance(value, list):
                memory_log["files_modified"] = len(value)
            else:
                memory_log.pop("files_modified")

    # Fix complexity - must be dict (Complexity model), not string
    if "complexity" in memory_log:
        if isinstance(memory_log["complexity"], str):
            memory_log.pop("complexity")

    # Fix solution - must be dict (Solution model), not string
    if "solution" in memory_log:
        if isinstance(memory_log["solution"], str):
            memory_log.pop("solution")

    return memory_log


def wrap_memory_log(raw_json: Dict[str, Any], user_id: str, project_id: str, session_id: str) -> Dict[str, Any]:
    """
    Wrap flat memory log JSON into required format.
    Pydantic will automatically drop fields not in the schema.
    """
    # Check if already wrapped
    if "memory_log" in raw_json:
        memory_log = sanitize_memory_log(raw_json["memory_log"])
        return {
            "user_id": raw_json.get("user_id", user_id),
            "project_id": raw_json.get("project_id", project_id),
            "session_id": raw_json.get("session_id", session_id),
            "memory_log": memory_log
        }

    # Flat format - wrap it
    memory_log = sanitize_memory_log(raw_json)
    return {
        "user_id": user_id,
        "project_id": project_id,
        "session_id": session_id,
        "memory_log": memory_log
    }


async def migrate_files(source_dir: Path, dry_run: bool, user_id: str, project_id: str, session_id: str):
    """Migrate all JSON files from source directory to PostgreSQL."""

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

                wrapped = wrap_memory_log(raw_json, user_id, project_id, session_id)

                # Validate with Pydantic (this will drop invalid fields)
                memory_log_create = MemoryLogCreate.model_validate(wrapped)

                print(f"✓ {json_file.name}")
                print(f"  Task: {memory_log_create.memory_log.task}")
                print(f"  Agent: {memory_log_create.memory_log.agent}")
                print(f"  Date: {memory_log_create.memory_log.date}")
                success_count += 1

            except ValidationError as e:
                print(f"✗ {json_file.name} - Validation Error:")
                print(f"  {e}")
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
            repo = MemoryLogRepository(session)

            for json_file in json_files:
                try:
                    with json_file.open("r", encoding="utf-8") as f:
                        raw_json = json.load(f)

                    wrapped = wrap_memory_log(raw_json, user_id, project_id, session_id)

                    # Validate with Pydantic (drops invalid fields automatically)
                    memory_log_create = MemoryLogCreate.model_validate(wrapped)

                    # Convert to format for database
                    task = memory_log_create.memory_log.task
                    agent = memory_log_create.memory_log.agent
                    date_dt = ensure_datetime(memory_log_create.memory_log.date)

                    # Build raw_data with system datetime
                    current_datetime_iso = datetime.utcnow().isoformat()
                    memory_log_dict = memory_log_create.memory_log.model_dump(exclude_none=True)

                    raw_data = {
                        "user_id": user_id,
                        "project_id": project_id,
                        "session_id": session_id,
                        "datetime": current_datetime_iso,
                        "memory_log": memory_log_dict
                    }

                    # Insert into database
                    memory_log = await repo.create(
                        task=task,
                        agent=agent,
                        date=date_dt,
                        raw_data=raw_data,
                        user_id=user_id,
                        project_id=project_id
                    )

                    print(f"✓ {json_file.name} -> ID: {memory_log.id}")
                    success_count += 1

                except ValidationError as e:
                    print(f"✗ {json_file.name} - Validation Error:")
                    print(f"  {e}")
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
        project_id=args.project_id,
        session_id=args.session_id
    ))


if __name__ == "__main__":
    main()

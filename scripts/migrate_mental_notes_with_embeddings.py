"""
Migrate mental note JSON files into PostgreSQL with pgvector embeddings.

Each JSON file can contain multiple entries; every entry becomes one row.
Session ID is intentionally set to NULL for all migrated notes (per request).

Usage examples:
    python scripts/migrate_mental_notes_with_embeddings.py --source mental_nots_temp
    python scripts/migrate_mental_notes_with_embeddings.py --source mental_nots_temp --dry-run
    python scripts/migrate_mental_notes_with_embeddings.py --limit 50
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

# Best-effort .env loader so DATABASE_URL is present even without python-dotenv
def load_dotenv() -> None:
    try:
        from dotenv import load_dotenv as _ld
        _ld()
        return
    except Exception:
        pass  # fall through to lightweight parser

    env_path = Path(".env")
    if not env_path.exists():
        return
    try:
        for line in env_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))
    except Exception:
        # Silence parsing issues; this is a best-effort fallback.
        return

# Ensure project root on path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.api.bootstrap.config import load_app_config, load_service_config
from src.database import DatabaseManager
from src.database.models import MentalNote
from src.modules.core import EventBus, Logger
from src.modules.embeddings import (
    EmbeddingService,
    GoogleEmbeddingProvider,
    ProviderConfig,
    EmbeddingCache,
)
from rich.console import Console

# Defaults
DEFAULT_USER_ID = "84e17260-ff03-409b-bf30-0b5ba52a2ab4"
DEFAULT_PROJECT_ID = "08fd3ab5-215c-4405-a5b6-17b2620e064"
DEFAULT_NOTE_TYPE = "note"
MAX_TEXT_SIZE_BYTES = 30000  # guardrail for provider limits (~36KB for Google)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Migrate mental note JSON files into Postgres with pgvector embeddings."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("mental_nots_temp"),
        help="Directory containing mental note JSON files.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional limit of files to process (0 = all).",
    )
    parser.add_argument(
        "--entry-limit",
        type=int,
        default=0,
        help="Optional limit of total entries to process across files (0 = all).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of rows to process before committing a batch (default: 100).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate and preview without writing to the database.",
    )
    parser.add_argument(
        "--skip-embedding",
        action="store_true",
        help="Insert rows without generating embeddings.",
    )
    parser.add_argument(
        "--user-id",
        default=DEFAULT_USER_ID,
        help=f"Fallback user_id (default: {DEFAULT_USER_ID}).",
    )
    parser.add_argument(
        "--project-id",
        default=DEFAULT_PROJECT_ID,
        help=f"Fallback project_id (default: {DEFAULT_PROJECT_ID}).",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=Path("backup"),
        help="Move each successfully migrated file into this directory (relative to source unless absolute).",
    )
    return parser.parse_args()


def parse_timestamp(value: Any) -> datetime:
    """Parse timestamp (supports milliseconds) into datetime; fallback to now()."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        # Entries use millisecond timestamps
        try:
            return datetime.fromtimestamp(float(value) / 1000.0)
        except Exception:
            pass
    if isinstance(value, str):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            pass
    return datetime.utcnow()


def _extract_value(data: Dict[str, Any], key: str) -> str:
    val = data.get(key)
    if isinstance(val, str):
        return val
    if isinstance(val, list):
        return " ".join([str(v) for v in val if v])
    if isinstance(val, dict):
        return " ".join([f"{k}: {v}" for k, v in val.items() if v])
    return ""


def prepare_mental_note_text(content: str, meta_data: Dict[str, Any]) -> str:
    """Build embedding text from content and metadata."""
    lines = [content]
    lines.append(_extract_value(meta_data, "summary"))
    lines.append(_extract_value(meta_data, "tags"))
    lines.append(_extract_value(meta_data, "category"))

    text = "\n".join([line.strip() for line in lines if line and line.strip()])
    if not text:
        text = json.dumps({"content": content, "meta_data": meta_data}, ensure_ascii=False)
    return text


def normalize_entry(
    entry: Dict[str, Any],
    defaults: argparse.Namespace,
    file_stem: str,
    fallback_timestamp: Any = None,
) -> Tuple[Dict[str, Any], datetime]:
    """
    Normalize a single entry from the temp JSON file to MentalNote fields.

    Session ID is intentionally set to None for all migrated notes.
    """
    content = entry.get("content") or ""
    note_type = entry.get("type") or DEFAULT_NOTE_TYPE
    meta_data = entry.get("metadata") or {}
    timestamp = entry.get("timestamp") or entry.get("time") or fallback_timestamp

    created_at = parse_timestamp(timestamp)

    normalized = {
        "session_id": None,  # per request: do not carry session identifiers
        "content": content,
        "note_type": note_type,
        "meta_data": meta_data if isinstance(meta_data, dict) else {},
        "user_id": defaults.user_id,
        "project_id": defaults.project_id,
    }
    return normalized, created_at


async def migrate(args: argparse.Namespace) -> None:
    console = Console()

    files = sorted(args.source.glob("*.json"))
    if args.limit and args.limit > 0:
        files = files[: args.limit]

    if not files:
        console.print(f"[red]No JSON files found in {args.source}[/red]")
        return

    console.print(f"[cyan]Found {len(files)} file(s). Mode: {'DRY-RUN' if args.dry_run else 'LIVE'}[/cyan]")

    backup_dir: Optional[Path] = None
    if args.backup_dir:
        backup_dir = args.backup_dir if args.backup_dir.is_absolute() else args.source / args.backup_dir
        backup_dir.mkdir(parents=True, exist_ok=True)

    load_dotenv()
    app_config = load_app_config()
    service_config = load_service_config()

    event_bus = EventBus()
    logger = Logger("mental-note-migration")

    embedding_service = None
    if not args.skip_embedding and service_config.embedding.is_available:
        embedding_config = ProviderConfig(
            provider_name=service_config.embedding.provider_name,
            model_name=service_config.embedding.model_name,
            api_key=service_config.embedding.api_key,
            timeout_seconds=service_config.embedding.timeout_seconds,
            max_retries=service_config.embedding.max_retries,
        )
        embedding_provider = GoogleEmbeddingProvider(embedding_config)
        embedding_cache = EmbeddingCache(
            max_size=service_config.embedding.cache_size,
            ttl_hours=service_config.embedding.cache_ttl_hours,
        )
        embedding_service = EmbeddingService(
            event_bus=event_bus,
            logger=logger,
            provider=embedding_provider,
            cache=embedding_cache,
            cache_enabled=service_config.embedding.cache_enabled,
        )
    elif args.skip_embedding:
        console.print("[yellow]Embedding generation is disabled by --skip-embedding.[/yellow]")
    else:
        console.print("[yellow]Embedding service unavailable (missing API key). Running without embeddings.[/yellow]")

    db_manager = DatabaseManager(app_config.database_url)

    inserted = 0
    errors = 0
    embedded = 0
    skipped_embeddings = 0
    processed_entries = 0

    if args.dry_run:
        for path in files:
            try:
                with path.open("r", encoding="utf-8") as f:
                    raw = json.load(f)

                entries = raw.get("entries") or []
                if not isinstance(entries, list):
                    raise ValueError("entries must be a list")

                for idx, entry in enumerate(entries):
                    if args.entry_limit and processed_entries >= args.entry_limit:
                        break
                    normalized, created_at = normalize_entry(
                        entry, args, path.stem, raw.get("startTime")
                    )
                    text = prepare_mental_note_text(normalized["content"], normalized["meta_data"])
                    byte_len = len(text.encode("utf-8"))
                    print(
                        f"[DRY] {path.name} entry#{idx} -> note_type={normalized['note_type']}, "
                        f"created_at={created_at.isoformat()}, text_bytes={byte_len}"
                    )
                    if not args.skip_embedding and byte_len > MAX_TEXT_SIZE_BYTES:
                        print(f"     embedding skipped (text too large: {byte_len} bytes)")
                    processed_entries += 1
            except Exception as e:
                errors += 1
                print(f"[DRY][ERROR] {path.name}: {e}")
            if args.entry_limit and processed_entries >= args.entry_limit:
                break
        console.print(f"[green]Dry-run complete.[/green] Files checked: {len(files)}, entries processed: {processed_entries}, errors: {errors}")
        return

    async with db_manager.session_factory() as session:
        for path in files:
            try:
                with path.open("r", encoding="utf-8") as f:
                    raw = json.load(f)

                entries = raw.get("entries") or []
                if not isinstance(entries, list):
                    raise ValueError("entries must be a list")

                for entry in entries:
                    if args.entry_limit and processed_entries >= args.entry_limit:
                        break
                    normalized, created_at = normalize_entry(
                        entry, args, path.stem, raw.get("startTime")
                    )

                    embedding_vector = None
                    if embedding_service:
                        text = prepare_mental_note_text(normalized["content"], normalized["meta_data"])
                        if text:
                            text_bytes = len(text.encode("utf-8"))
                            if text_bytes > MAX_TEXT_SIZE_BYTES:
                                skipped_embeddings += 1
                                logger.warning(f"[EMBED][SKIP] {path.name} text too large ({text_bytes} bytes)")
                            else:
                                resp = await embedding_service.generate_embedding(text)
                                embedding_vector = resp.embedding
                                embedded += 1
                        else:
                            skipped_embeddings += 1
                            logger.warning(f"[EMBED][SKIP] {path.name} empty text")

                    model = MentalNote(
                        session_id=None,  # explicit null per migration request
                        content=normalized["content"],
                        note_type=normalized["note_type"],
                        meta_data=normalized["meta_data"],
                        user_id=normalized["user_id"],
                        project_id=normalized["project_id"],
                        embedding=embedding_vector,
                        created_at=created_at,
                    )
                    session.add(model)
                    inserted += 1
                    processed_entries += 1
                    logger.info(f"[INSERT] {path.name} -> {model.note_type} @ {created_at.isoformat()}")

                    if args.batch_size and inserted % args.batch_size == 0:
                        await session.commit()
                        logger.info(f"[COMMIT] Batch committed at {inserted} inserts")
                        console.log(f"[blue]Batch commit[/blue] at insert #{inserted} (entries processed: {processed_entries})")

                # Move processed file to backup dir (only on success)
                if backup_dir:
                    target = backup_dir / path.name
                    path.replace(target)
            except Exception as e:
                errors += 1
                logger.error(f"[ERROR] {path.name}: {e}")
                console.print(f"[red][ERROR] {path.name}: {e}[/red]")
            if args.entry_limit and processed_entries >= args.entry_limit:
                break

        try:
            await session.commit()
            console.print(f"[green]Final commit successful.[/green]")
        except Exception as e:
            console.print(f"[red]Final commit failed: {e}[/red]")
            logger.error(f"[COMMIT][ERROR] {e}")

    await db_manager.close()
    console.print(
        f"[bold green]Migration complete.[/bold green] processed_files={len(files)}, inserted_rows={inserted}, "
        f"embedded={embedded}, skipped_embeddings={skipped_embeddings}, entries_processed={processed_entries}, errors={errors}"
    )


def main() -> None:
    args = parse_args()
    if not args.source.exists():
        print(f"Source directory not found: {args.source}")
        return
    asyncio.run(migrate(args))


if __name__ == "__main__":
    main()

"""
Migrate memory log JSON files into PostgreSQL and store pgvector embeddings.

Features:
- Accepts wrapped or flat memory log JSON payloads.
- Normalizes into MemoryLogCreate schema (task/agent at top level).
- Generates embeddings via EmbeddingService and writes directly to pgvector column.
- Supports dry-run, limit, and optional embedding skip.

Usage examples:
    python scripts/migrate_memory_logs_with_embeddings.py --source temp/memory_logs
    python scripts/migrate_memory_logs_with_embeddings.py --source temp/memory_logs --dry-run
    python scripts/migrate_memory_logs_with_embeddings.py --limit 50
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    def load_dotenv():
        return None

# Ensure project root on path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.api.bootstrap.config import load_app_config, load_service_config
from src.api.schemas.memory_log import MemoryLogCreate
from src.database import DatabaseManager
from src.database.models import MemoryLog
from src.modules.core import EventBus, Logger
from src.modules.embeddings import (
    EmbeddingService,
    GoogleEmbeddingProvider,
    ProviderConfig,
    EmbeddingCache,
)

# Defaults
DEFAULT_USER_ID = "84e17260-ff03-409b-bf30-0b5ba52a2ab4"
DEFAULT_PROJECT_ID = "semntix-code"
DEFAULT_SESSION_ID = "migration"
DEFAULT_AGENT = "unknown-agent"
DEFAULT_TASK_PREFIX = "memory-log"
MAX_TEXT_SIZE_BYTES = 30000  # guardrail for provider limits (~36KB for Google)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Migrate memory log JSON files into Postgres with pgvector embeddings."
    )
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("temp") / "memory_logs",
        help="Directory containing memory log JSON files.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional limit of files to process (0 = all).",
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
        "--session-id",
        default=DEFAULT_SESSION_ID,
        help=f"Fallback session_id (default: {DEFAULT_SESSION_ID}).",
    )
    parser.add_argument(
        "--default-agent",
        default=DEFAULT_AGENT,
        help=f"Fallback agent if missing (default: {DEFAULT_AGENT}).",
    )
    parser.add_argument(
        "--task-prefix",
        default=DEFAULT_TASK_PREFIX,
        help=f"Prefix used when deriving task from filename (default: {DEFAULT_TASK_PREFIX}).",
    )
    parser.add_argument(
        "--backup-dir",
        type=Path,
        default=None,
        help="If set, move each successfully migrated file into this directory (relative to source unless absolute).",
    )
    return parser.parse_args()


def parse_datetime(value: Any) -> datetime:
    """Parse various timestamp formats; fall back to now()."""
    if isinstance(value, datetime):
        return value
    if isinstance(value, (int, float)):
        try:
            return datetime.fromtimestamp(value)
        except Exception:
            pass
    if isinstance(value, str):
        for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            pass
    return datetime.utcnow()


def normalize_payload(
    raw: Dict[str, Any],
    file_stem: str,
    defaults: argparse.Namespace,
) -> Tuple[Dict[str, Any], datetime]:
    """
    Normalize arbitrary payload into MemoryLogCreate-friendly structure.

    Returns:
        (payload_for_pydantic, created_at_datetime)
    """
    wrapped = raw if "memory_log" in raw else {"memory_log": raw}

    memory_log = wrapped.get("memory_log") or {}
    memory_log = dict(memory_log) if isinstance(memory_log, dict) else {}

    # Capture agent/task before we strip meta keys from the inner payload
    agent_from_inner = memory_log.get("agent")
    task_from_inner = memory_log.get("task") or memory_log.get("id")

    # Remove wrapper/meta keys from the inner payload
    for key in ("memory_log", "user_id", "project_id", "session_id", "task", "agent", "embedding"):
        memory_log.pop(key, None)

    user_id = wrapped.get("user_id") or defaults.user_id
    project_id = wrapped.get("project_id") or defaults.project_id
    session_id = wrapped.get("session_id") or wrapped.get("sessionId") or defaults.session_id

    task = (
        wrapped.get("task")
        or task_from_inner
        or f"{defaults.task_prefix}-{file_stem}"
    )
    agent = wrapped.get("agent") or agent_from_inner or defaults.default_agent

    timestamp_source = (
        wrapped.get("datetime")
        or wrapped.get("date")
        or memory_log.get("datetime")
        or memory_log.get("date")
    )
    created_at = parse_datetime(timestamp_source)

    # Keep original timestamp inside payload for provenance
    memory_log.setdefault("datetime", created_at.isoformat())

    normalized = {
        "user_id": user_id,
        "project_id": project_id,
        "session_id": session_id,
        "task": task,
        "agent": agent,
        "memory_log": sanitize_memory_log(memory_log),
    }
    return normalized, created_at


def _extract_value(data: Dict[str, Any], key: str) -> str:
    val = data.get(key)
    if isinstance(val, str):
        return val
    if isinstance(val, list):
        return " ".join([str(v) for v in val if v])
    if isinstance(val, dict):
        return " ".join([f"{k}: {v}" for k, v in val.items() if v])
    return ""


def prepare_memory_log_text(memory_log: Dict[str, Any]) -> str:
    """Build embedding text from a memory_log dict."""
    lines = []
    lines.append(_extract_value(memory_log, "summary"))
    lines.append(_extract_value(memory_log, "content"))
    lines.append(_extract_value(memory_log, "task"))
    lines.append(_extract_value(memory_log, "agent"))
    lines.append(_extract_value(memory_log, "files_touched"))
    lines.append(_extract_value(memory_log, "tags"))
    lines.append(_extract_value(memory_log, "validation"))

    solution = memory_log.get("solution") or {}
    if isinstance(solution, dict):
        lines.append(_extract_value(solution, "approach"))
        lines.append(_extract_value(solution, "key_changes"))

    outcomes = memory_log.get("outcomes") or {}
    if isinstance(outcomes, dict):
        lines.append(_extract_value(outcomes, "performance_impact"))
        lines.append(_extract_value(outcomes, "test_coverage_delta"))
        lines.append(_extract_value(outcomes, "technical_debt_reduced"))

    gotchas = memory_log.get("gotchas")
    if isinstance(gotchas, list):
        for g in gotchas:
            if isinstance(g, dict):
                lines.append(_extract_value(g, "issue"))
                lines.append(_extract_value(g, "solution"))

    text = "\n".join([line.strip() for line in lines if line and line.strip()])
    if not text and memory_log:
        text = json.dumps(memory_log, ensure_ascii=False)
    return text


def _coerce_bool(value: Any) -> Optional[bool]:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        low = value.strip().lower()
        if low.startswith("true"):
            return True
        if low.startswith("false"):
            return False
    return None


def sanitize_memory_log(memory_log: Dict[str, Any]) -> Dict[str, Any]:
    """Normalize fields so Pydantic validation passes."""
    data = dict(memory_log)

    # Coerce content/summary/root_cause dicts to strings
    for key in ("content", "summary", "root_cause"):
        if isinstance(data.get(key), dict):
            data[key] = json.dumps(data[key], ensure_ascii=False)

    # files_modified allows str or int; convert list/dict to len
    if "files_modified" in data:
        val = data["files_modified"]
        if isinstance(val, list):
            data["files_modified"] = len(val)
        elif isinstance(val, dict):
            data["files_modified"] = len(val)

    # outcomes.follow_up_needed: parse boolean-ish strings
    outcomes = data.get("outcomes")
    if isinstance(outcomes, dict):
        coerced = _coerce_bool(outcomes.get("follow_up_needed"))
        if coerced is not None:
            outcomes["follow_up_needed"] = coerced
        elif "follow_up_needed" in outcomes:
            outcomes.pop("follow_up_needed")
        data["outcomes"] = outcomes

    # solution: if string, tuck into approach
    if isinstance(data.get("solution"), str):
        data["solution"] = {"approach": data["solution"]}

    # gotchas: if list of strings, wrap into dicts
    if isinstance(data.get("gotchas"), list):
        new_gotchas = []
        for g in data["gotchas"]:
            if isinstance(g, str):
                new_gotchas.append({"issue": g})
            elif isinstance(g, dict):
                new_gotchas.append(g)
        data["gotchas"] = new_gotchas

    return data


async def migrate(args: argparse.Namespace) -> None:
    files = sorted(args.source.glob("*.json"))
    if args.limit and args.limit > 0:
        files = files[: args.limit]

    if not files:
        print(f"No JSON files found in {args.source}")
        return

    print(f"Found {len(files)} file(s). Mode: {'DRY-RUN' if args.dry_run else 'LIVE'}")

    backup_dir: Optional[Path] = None
    if args.backup_dir:
        backup_dir = args.backup_dir if args.backup_dir.is_absolute() else args.source / args.backup_dir
        backup_dir.mkdir(parents=True, exist_ok=True)

    load_dotenv()
    app_config = load_app_config()
    service_config = load_service_config()

    event_bus = EventBus()
    logger = Logger("memory-log-migration")

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
        print("Embedding generation is disabled by --skip-embedding.")
    else:
        print("Embedding service unavailable (missing API key). Running without embeddings.")

    db_manager = DatabaseManager(app_config.database_url)

    inserted = 0
    errors = 0
    embedded = 0
    skipped_embeddings = 0

    if args.dry_run:
        for path in files:
            try:
                with path.open("r", encoding="utf-8") as f:
                    raw = json.load(f)
                normalized, created_at = normalize_payload(raw, path.stem, args)
                memory_log_create = MemoryLogCreate.model_validate(normalized)
                memory_log_dict = memory_log_create.memory_log.model_dump(exclude_none=True)
                text = prepare_memory_log_text(memory_log_dict)
                byte_len = len(text.encode("utf-8"))
                print(f"[DRY] {path.name} -> task={memory_log_create.task}, agent={memory_log_create.agent}, created_at={created_at.isoformat()}, text_bytes={byte_len}")
                if not args.skip_embedding and byte_len > MAX_TEXT_SIZE_BYTES:
                    print(f"     embedding skipped (text too large: {byte_len} bytes)")
            except Exception as e:
                errors += 1
                print(f"[DRY][ERROR] {path.name}: {e}")
        print(f"Dry-run complete. Files checked: {len(files)}, errors: {errors}")
        return

    async with db_manager.session_factory() as session:
        for path in files:
            try:
                with path.open("r", encoding="utf-8") as f:
                    raw = json.load(f)

                normalized, created_at = normalize_payload(raw, path.stem, args)
                memory_log_create = MemoryLogCreate.model_validate(normalized)
                memory_log_dict = memory_log_create.memory_log.model_dump(exclude_none=True)

                embedding_vector = None
                if embedding_service:
                    text = prepare_memory_log_text(memory_log_dict)
                    if text:
                        if len(text.encode("utf-8")) > MAX_TEXT_SIZE_BYTES:
                            skipped_embeddings += 1
                            logger.warning(f"[EMBED][SKIP] {path.name} text too large ({len(text.encode('utf-8'))} bytes)")
                        else:
                            resp = await embedding_service.generate_embedding(text)
                            embedding_vector = resp.embedding
                            embedded += 1
                    else:
                        skipped_embeddings += 1
                        logger.warning(f"[EMBED][SKIP] {path.name} empty text")

                model = MemoryLog(
                    task=memory_log_create.task,
                    agent=memory_log_create.agent,
                    session_id=memory_log_create.session_id,
                    memory_log=memory_log_dict,
                    user_id=memory_log_create.user_id,
                    project_id=memory_log_create.project_id,
                    embedding=embedding_vector,
                    created_at=created_at,
                )
                session.add(model)
                inserted += 1
                logger.info(f"[INSERT] {path.name} -> {model.task}")

                # Move processed file to backup dir (only on success)
                if backup_dir:
                    target = backup_dir / path.name
                    path.replace(target)
            except Exception as e:
                errors += 1
                logger.error(f"[ERROR] {path.name}: {e}")

        await session.commit()

    await db_manager.close()
    print(
        f"Migration complete. processed={len(files)}, inserted={inserted}, embedded={embedded}, "
        f"skipped_embeddings={skipped_embeddings}, errors={errors}"
    )


def main() -> None:
    args = parse_args()
    if not args.source.exists():
        print(f"Source directory not found: {args.source}")
        return
    asyncio.run(migrate(args))


if __name__ == "__main__":
    main()

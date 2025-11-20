"""
Ingest migrated memory logs into PostgreSQL and trigger vectorization.

Reads JSON files (wrapped or flat) from a directory, normalizes them into
MemoryLogCreate, creates memory_logs rows, and emits memory_log.stored so the
existing event handlers generate embeddings and store vectors.

Defaults:
- Source: data/memory_logs_migrate/proceed/memory_logs/*.json
- Uses the same initialization flow as the FastAPI app (core services,
  embedding service, event handlers, DatabaseManager).
"""

import argparse
import asyncio
import json
import sys
from datetime import datetime, date
from pathlib import Path
from typing import List, Any, Dict

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    def load_dotenv():
        return None

# Ensure project root is on path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.api.bootstrap.config import load_app_config, load_service_config
from src.api.dependencies.event_handlers import initialize_event_handlers
from src.api.schemas.memory_log import MemoryLogCreate
from src.database import DatabaseManager
from src.services.memory_log_ingestor import ingest_memory_log
from src.modules.core import EventBus, Logger
from src.modules.embeddings import (
    EmbeddingService,
    GoogleEmbeddingProvider,
    ProviderConfig,
    EmbeddingCache,
)


DEFAULT_USER_ID = "84e17260-ff03-409b-bf30-0b5ba52a2ab4"
DEFAULT_PROJECT_ID = "semntix-code"
DEFAULT_SESSION_ID = "000-000-000-000"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest migrated memory logs and trigger vectorization.")
    parser.add_argument(
        "--source",
        type=Path,
        default=Path("data") / "memory_logs_migrate" / "proceed" / "memory_logs",
        help="Directory containing memory log JSON files (wrapped or flat).",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=0,
        help="Optional limit of files to ingest (0 = all).",
    )
    parser.add_argument("--user-id", default=DEFAULT_USER_ID, help="User ID to inject if missing.")
    parser.add_argument("--project-id", default=DEFAULT_PROJECT_ID, help="Project ID to inject if missing.")
    parser.add_argument("--session-id", default=DEFAULT_SESSION_ID, help="Session ID to inject if missing.")
    parser.add_argument(
        "--skip-vectorization",
        action="store_true",
        help="Do not emit memory_log.stored events (no embedding/vector storage).",
    )
    return parser.parse_args()


def ensure_datetime_from_date(date_value: Any) -> str:
    """Convert date-like values to ISO datetime with midnight time; fall back to now()."""
    if isinstance(date_value, datetime):
        return date_value.isoformat()
    if isinstance(date_value, date):
        return datetime.combine(date_value, datetime.min.time()).isoformat()
    if isinstance(date_value, str):
        for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
            try:
                dt = datetime.strptime(date_value, fmt)
                return dt.isoformat()
            except ValueError:
                continue
        try:
            return datetime.fromisoformat(date_value.replace("Z", "+00:00")).isoformat()
        except ValueError:
            pass
    return datetime.utcnow().isoformat()


def normalize_payload(
    payload: Dict[str, Any],
    user_id: str,
    project_id: str,
    session_id: str,
) -> Dict[str, Any]:
    """
    Ensure payload conforms to MemoryLogCreate. Supports:
    - Already-wrapped payloads with top-level user_id/project_id/memory_log.
    - Flat memory_log dict (task/agent/date...) which will be wrapped.
    """
    if "memory_log" in payload:
        wrapped = dict(payload)
        wrapped["user_id"] = wrapped.get("user_id") or user_id
        wrapped["project_id"] = wrapped.get("project_id") or project_id
        wrapped["session_id"] = wrapped.get("session_id") or session_id
        if "datetime" not in wrapped:
            # Derive from inner date if possible
            dl = wrapped.get("memory_log", {}).get("date")
            wrapped["datetime"] = ensure_datetime_from_date(dl)
        return wrapped

    # Flat form: treat payload as memory_log
    memory_log = dict(payload)
    date_val = memory_log.get("date")
    return {
        "user_id": user_id,
        "project_id": project_id,
        "session_id": session_id,
        "datetime": ensure_datetime_from_date(date_val),
        "memory_log": memory_log,
    }


async def ingest_files(
    files: List[Path],
    user_id: str,
    project_id: str,
    session_id: str,
    skip_vectorization: bool,
) -> None:
    load_dotenv()

    app_config = load_app_config()
    service_config = load_service_config()

    event_bus = EventBus()
    logger = Logger("semantic-bridge-server")
    embedding_service = None
    if service_config.embedding.is_available:
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
        logger.info("Embedding service initialized for ingestion script")
    else:
        logger.warning("Embedding disabled (missing API key) - vectorization handlers will fail if invoked.")
    db_manager = DatabaseManager(app_config.database_url)

    # Register handlers so memory_log.stored triggers vectorization
    if not skip_vectorization and embedding_service:
        initialize_event_handlers(
            event_bus=event_bus,
            logger=logger,
            db_session_factory=db_manager.session_factory,
            embedding_service=embedding_service,
        )
    else:
        logger.warning("Vectorization disabled for ingestion (skip_vectorization or missing embedding service).")

    ingested = 0

    async with db_manager.session_factory() as session:
        for path in files:
            try:
                with path.open("r", encoding="utf-8") as f:
                    payload = json.load(f)
                normalized = normalize_payload(payload, user_id, project_id, session_id)
                model = MemoryLogCreate.model_validate(normalized)
                await ingest_memory_log(
                    model,
                    session,
                    event_bus,
                    logger,
                    emit_event=not skip_vectorization and embedding_service is not None,
                )
                ingested += 1
                logger.info(f"[INGEST] OK: {path.name}")
            except Exception as e:
                logger.error(f"[INGEST] FAILED: {path.name} ({e})", exc_info=False)

        # Commit once after batch
        await session.commit()

    await db_manager.close()
    logger.info(f"Ingestion complete. Files processed: {len(files)}, ingested: {ingested}")


def main() -> None:
    args = parse_args()
    source_dir = args.source

    if not source_dir.exists():
        print(f"Source directory not found: {source_dir}")
        return

    files = sorted(source_dir.glob("*.json"))
    if args.limit and args.limit > 0:
        files = files[: args.limit]

    if not files:
        print(f"No JSON files found in {source_dir}")
        return

    print(f"Found {len(files)} files. Starting ingestion...")
    asyncio.run(
        ingest_files(
            files,
            args.user_id,
            args.project_id,
            args.session_id,
            args.skip_vectorization,
        )
    )


if __name__ == "__main__":
    main()

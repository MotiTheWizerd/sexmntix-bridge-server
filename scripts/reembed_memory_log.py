"""
Re-embed a specific memory log using the curated payload extractor.

Usage:
    python scripts/reembed_memory_log.py <memory_log_id>
    python scripts/reembed_memory_log.py <memory_log_id> --dry-run --show-text
    python scripts/reembed_memory_log.py <memory_log_id> --skip-vector
"""

import argparse
import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, Optional

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional dependency
    def load_dotenv():
        return None


# Ensure project root on sys.path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.api.bootstrap.config import load_app_config, load_service_config  # noqa: E402
from src.database import DatabaseManager  # noqa: E402
from src.database.models import MemoryLog  # noqa: E402
from src.modules.core import EventBus, Logger  # noqa: E402
from src.modules.embeddings import (  # noqa: E402
    EmbeddingService,
    ProviderConfig,
    EmbeddingCache,
    GoogleEmbeddingProvider,
)
from src.modules.vector_storage.text_extraction import MemoryTextExtractor  # noqa: E402
from src.infrastructure.chromadb.client import ChromaDBClient  # noqa: E402
from src.infrastructure.chromadb.repository import VectorRepository  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Re-embed a specific memory log by ID")
    parser.add_argument("memory_log_id", help="UUID/ID of the memory log to re-embed")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Extract and preview embedding text without writing to DB/ChromaDB",
    )
    parser.add_argument(
        "--skip-vector",
        action="store_true",
        help="Skip updating the ChromaDB vector store",
    )
    parser.add_argument(
        "--skip-db",
        action="store_true",
        help="Skip updating the PostgreSQL embedding column",
    )
    parser.add_argument(
        "--show-text",
        action="store_true",
        help="Print the curated embedding text payload",
    )
    parser.add_argument(
        "--preview-length",
        type=int,
        default=400,
        help="Number of characters to show for text preview (default: 400)",
    )
    return parser.parse_args()


async def fetch_memory_log(
    db_manager: DatabaseManager,
    memory_log_id: str,
) -> Optional[Dict[str, Any]]:
    async with db_manager.session_factory() as session:
        record = await session.get(MemoryLog, memory_log_id)
        if not record:
            return None

        return {
            "id": record.id,
            "task": record.task,
            "agent": record.agent,
            "user_id": record.user_id,
            "project_id": record.project_id,
            "memory_log": record.memory_log or {},
            "created_at": record.created_at,
            "session_id": record.session_id,
        }


async def update_postgres_embedding(
    db_manager: DatabaseManager,
    memory_log_id: str,
    embedding: list[float],
) -> None:
    async with db_manager.session_factory() as session:
        record = await session.get(MemoryLog, memory_log_id)
        if not record:
            raise RuntimeError(f"Memory log {memory_log_id} not found during update")
        record.embedding = embedding
        await session.commit()


async def store_in_chromadb(
    vector_repository: VectorRepository,
    memory_log_id: str,
    embedding: list[float],
    memory_log_payload: Dict[str, Any],
    searchable_text: str,
    user_id: str,
    project_id: str,
) -> str:
    metadata = memory_log_payload.get("metadata", {})
    if not isinstance(metadata, dict):
        metadata = {}

    structured_document = {
        "memory_log": memory_log_payload,
        "content": searchable_text,
        "metadata": {
            "document_type": "memory_log",
            "memory_log_id": memory_log_id,
            **metadata,
        },
    }

    memory_id = await vector_repository.add_memory(
        memory_log_id=memory_log_id,
        embedding=embedding,
        memory_data=structured_document,
        user_id=user_id,
        project_id=project_id,
    )
    return memory_id


async def reembed_memory_log(args: argparse.Namespace) -> None:
    load_dotenv()
    app_config = load_app_config()
    service_config = load_service_config()

    if not service_config.embedding.is_available:
        raise RuntimeError("Embedding service unavailable. Configure GOOGLE_API_KEY before running.")

    db_manager = DatabaseManager(app_config.database_url)
    logger = Logger("memory-log-reembed")
    event_bus = EventBus()
    extractor = MemoryTextExtractor(logger)

    dry_run = args.dry_run
    skip_vector = args.skip_vector or dry_run
    skip_db = args.skip_db or dry_run

    record = await fetch_memory_log(db_manager, args.memory_log_id)
    if not record:
        raise RuntimeError(f"Memory log {args.memory_log_id} was not found in PostgreSQL.")

    if not record["user_id"] or not record["project_id"]:
        raise RuntimeError(
            f"Memory log {args.memory_log_id} is missing user_id/project_id and cannot be re-embedded."
        )

    searchable_text = extractor.extract_with_fallback(record["memory_log"], record["id"])
    if not searchable_text:
        raise RuntimeError(f"Memory log {record['id']} produced empty searchable text.")

    preview = searchable_text[: args.preview_length]
    payload_size = len(searchable_text.encode("utf-8"))

    print("\nMemory Log Re-embedding")
    print("=" * 60)
    print(f"ID: {record['id']}")
    print(f"Task: {record['task']}")
    print(f"User/Project: {record['user_id']} / {record['project_id']}")
    print(f"Payload size: {payload_size:,} bytes")
    print(f"Preview ({len(preview)} chars): {preview}")

    if args.show_text:
        print("\n--- Curated Embedding Text ---")
        print(searchable_text)
        print("--- End ---\n")

    if dry_run:
        print("Dry run complete (no embedding generated).")
        await db_manager.close()
        return

    provider_config = ProviderConfig(
        provider_name=service_config.embedding.provider_name,
        model_name=service_config.embedding.model_name,
        api_key=service_config.embedding.api_key,
        timeout_seconds=service_config.embedding.timeout_seconds,
        max_retries=service_config.embedding.max_retries,
    )

    provider = GoogleEmbeddingProvider(provider_config)
    embedding_service: Optional[EmbeddingService] = None

    try:
        embedding_service = EmbeddingService(
            event_bus=event_bus,
            logger=logger,
            provider=provider,
            cache=EmbeddingCache(
                max_size=service_config.embedding.cache_size,
                ttl_hours=service_config.embedding.cache_ttl_hours,
            ),
            cache_enabled=service_config.embedding.cache_enabled,
        )

        embedding_response = await embedding_service.generate_embedding(searchable_text)
        embedding_vector = embedding_response.embedding
        print(f"\nGenerated embedding: {len(embedding_vector)} dimensions (cached={embedding_response.cached})")

        if not skip_db:
            await update_postgres_embedding(db_manager, record["id"], embedding_vector)
            print("PostgreSQL embedding column updated.")
        else:
            print("Skipped PostgreSQL update.")

        if not skip_vector:
            chromadb_client = ChromaDBClient(storage_path=service_config.chromadb.base_path)
            vector_repo = VectorRepository(chromadb_client)
            memory_id = await store_in_chromadb(
                vector_repository=vector_repo,
                memory_log_id=record["id"],
                embedding=embedding_vector,
                memory_log_payload=record["memory_log"],
                searchable_text=searchable_text,
                user_id=record["user_id"],
                project_id=record["project_id"],
            )
            print(f"ChromaDB vector updated (memory_id={memory_id}).")
        else:
            print("Skipped ChromaDB update.")

    finally:
        if embedding_service is not None:
            await embedding_service.close()
        await db_manager.close()


def main():
    args = parse_args()
    asyncio.run(reembed_memory_log(args))


if __name__ == "__main__":
    main()

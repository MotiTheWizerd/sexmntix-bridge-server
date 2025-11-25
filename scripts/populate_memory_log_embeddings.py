"""
Populate embeddings for memory logs that don't have them yet.

This script:
1. Queries memory_logs with NULL embeddings from PostgreSQL
2. Extracts text from memory_log JSON payloads
3. Generates embeddings using EmbeddingService
4. Updates PostgreSQL with the embeddings
5. Supports dry-run, batching, and resumability (offset-based)

Usage:
    python scripts/populate_memory_log_embeddings.py --dry-run
    python scripts/populate_memory_log_embeddings.py
    python scripts/populate_memory_log_embeddings.py --resume
    python scripts/populate_memory_log_embeddings.py --batch-size 25
    python scripts/populate_memory_log_embeddings.py --limit 100
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        return None

# Fix Windows console encoding
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure project root is on path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from sqlalchemy import text as sql_text, select, func
from src.api.bootstrap.config import load_app_config, load_service_config
from src.database import DatabaseManager
from src.database.models import MemoryLog
from src.modules.core import EventBus, Logger
from src.modules.embeddings import (
    EmbeddingService,
    GoogleEmbeddingProvider,
    ProviderConfig,
    EmbeddingCache,
)


BATCH_SIZE = 50
PROGRESS_FILE = Path(__file__).parent / "memory_log_embedding_progress.json"
DELAY_BETWEEN_BATCHES = 1.0  # seconds
MAX_TEXT_SIZE_BYTES = 30000  # 30KB safety margin (Google API limit ~36KB)


class ProgressTracker:
    """Track progress for resumability."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        if self.file_path.exists():
            try:
                with open(self.file_path, "r") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Warning: Could not load progress file: {e}")

        return {
            "last_offset": 0,
            "total_processed": 0,
            "total_errors": 0,
            "total_skipped": 0,
            "last_run": None,
            "failed_ids": [],
            "oversized_ids": [],
        }

    def save(self):
        try:
            self.data["last_run"] = datetime.utcnow().isoformat()
            with open(self.file_path, "w") as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save progress file: {e}")

    def update(self, processed: int = 0, errors: int = 0, skipped: int = 0, offset: int = None):
        self.data["total_processed"] += processed
        self.data["total_errors"] += errors
        self.data["total_skipped"] += skipped
        if offset is not None:
            self.data["last_offset"] = offset
        self.save()

    def add_failed_id(self, memory_log_id: str):
        if memory_log_id not in self.data["failed_ids"]:
            self.data["failed_ids"].append(memory_log_id)
        self.save()

    def add_oversized_id(self, memory_log_id: str):
        if memory_log_id not in self.data["oversized_ids"]:
            self.data["oversized_ids"].append(memory_log_id)
        self.save()

    def reset(self):
        self.data = {
            "last_offset": 0,
            "total_processed": 0,
            "total_errors": 0,
            "total_skipped": 0,
            "last_run": None,
            "failed_ids": [],
            "oversized_ids": [],
        }
        self.save()


def parse_args():
    parser = argparse.ArgumentParser(description="Populate memory log embeddings")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing embeddings")
    parser.add_argument("--batch-size", type=int, default=BATCH_SIZE, help=f"Batch size (default: {BATCH_SIZE})")
    parser.add_argument("--limit", type=int, default=None, help="Max total records to process")
    parser.add_argument("--resume", action="store_true", help="Resume from last offset in progress file")
    parser.add_argument("--start-from", type=int, default=None, help="Start from a specific offset (overrides --resume)")
    parser.add_argument("--delay", type=float, default=DELAY_BETWEEN_BATCHES, help="Delay between batches in seconds")
    parser.add_argument("--reset-progress", action="store_true", help="Reset progress file before running")
    return parser.parse_args()


def _extract_value(data: Dict[str, Any], key: str) -> str:
    val = data.get(key)
    if isinstance(val, str):
        return val
    if isinstance(val, list):
        return " ".join([str(v) for v in val if v])
    if isinstance(val, dict):
        return " ".join([f"{k}: {v}" for k, v in val.items() if v])
    return ""


def prepare_memory_log_text(memory_log: MemoryLog) -> str:
    """
    Extract meaningful text from the memory_log JSON payload.
    """
    body = memory_log.memory_log or {}
    lines: List[str] = []

    # Primary fields
    lines.append(_extract_value(body, "summary"))
    lines.append(_extract_value(body, "content"))
    lines.append(_extract_value(body, "task"))
    lines.append(_extract_value(body, "agent"))

    # Optional nested fields
    lines.append(_extract_value(body, "files_touched"))
    lines.append(_extract_value(body, "tags"))
    lines.append(_extract_value(body, "validation"))

    solution = body.get("solution") or {}
    if isinstance(solution, dict):
        lines.append(_extract_value(solution, "approach"))
        lines.append(_extract_value(solution, "key_changes"))

    outcomes = body.get("outcomes") or {}
    if isinstance(outcomes, dict):
        lines.append(_extract_value(outcomes, "performance_impact"))
        lines.append(_extract_value(outcomes, "test_coverage_delta"))
        lines.append(_extract_value(outcomes, "technical_debt_reduced"))

    gotchas = body.get("gotchas")
    if isinstance(gotchas, list):
        for g in gotchas:
            if isinstance(g, dict):
                lines.append(_extract_value(g, "issue"))
                lines.append(_extract_value(g, "solution"))

    # Fallback: include whole JSON if still empty
    text = "\n".join([line.strip() for line in lines if line and line.strip()])
    if not text and body:
        text = json.dumps(body, ensure_ascii=False)

    return text


async def update_memory_log_embedding(db_manager: DatabaseManager, memory_log_id: str, embedding: List[float]) -> bool:
    """
    Update memory_logs.embedding using raw SQL for pgvector.
    """
    try:
        async with db_manager.session_factory() as session:
            vector_str = f"[{','.join(map(str, embedding))}]"
            sql = sql_text(
                "UPDATE memory_logs SET embedding = :vector WHERE id = :id"
            )
            await session.execute(sql, {"vector": vector_str, "id": memory_log_id})
            await session.commit()
            return True
    except Exception as e:
        print(f"    Database update failed: {e}")
        return False


async def populate_embeddings(
    dry_run: bool,
    batch_size: int,
    limit: Optional[int],
    resume: bool,
    start_from: Optional[int],
    delay: float,
    reset_progress: bool,
):
    print("\nMemory Log Embeddings Population Script")
    print("=" * 70)
    print()

    progress = ProgressTracker(PROGRESS_FILE)

    if reset_progress:
        print("Resetting progress file...")
        progress.reset()
        print()

    if start_from is not None:
        current_offset = start_from
        print(f"Starting from offset: {current_offset} (manual override)")
    elif resume:
        current_offset = progress.data["last_offset"]
        print(f"Resuming from offset: {current_offset}")
    else:
        current_offset = 0
        print("Starting from beginning (offset: 0)")

    print("Mode:", "DRY RUN" if dry_run else "LIVE")
    print()

    load_dotenv()
    app_config = load_app_config()
    service_config = load_service_config()

    if not service_config.embedding.is_available:
        print("Error: Embedding service not available (check GOOGLE_API_KEY)")
        sys.exit(1)

    db_manager = DatabaseManager(app_config.database_url)

    async with db_manager.session_factory() as session:
        total_without_embeddings = await session.scalar(
            select(func.count(MemoryLog.id)).where(MemoryLog.embedding.is_(None))
        )

    print(f"Total memory logs without embeddings: {total_without_embeddings}")

    if not total_without_embeddings:
        print("\nNo memory logs need embeddings. Exiting.")
        await db_manager.close()
        return

    remaining = total_without_embeddings - current_offset
    if limit:
        to_process = min(remaining, limit)
        print(f"Will process: {to_process} memory logs (limit: {limit})")
    else:
        to_process = remaining
        print(f"Will process: {to_process} memory logs (all remaining)")

    print()

    if dry_run:
        async with db_manager.session_factory() as session:
            result = await session.execute(
                select(MemoryLog)
                .where(MemoryLog.embedding.is_(None))
                .order_by(MemoryLog.created_at)
                .offset(current_offset)
                .limit(min(5, to_process))
            )
            sample_logs = list(result.scalars().all())

            if sample_logs:
                print("Sample memory logs:")
                for i, log in enumerate(sample_logs, 1):
                    text = prepare_memory_log_text(log)
                    print(f"\n{i}. MemoryLog ID: {log.id}")
                    print(f"   Task: {log.task}")
                    print(f"   Agent: {log.agent}")
                    print(f"   User: {log.user_id}")
                    print(f"   Project: {log.project_id}")
                    print(f"   Text length: {len(text)} chars")
                    print(f"   Created: {log.created_at}")

                num_batches = (to_process + batch_size - 1) // batch_size
                print(f"\nWould process in {num_batches} batch(es) of {batch_size}")
                print(f"With {delay}s delay between batches")
                print(f"Estimated time: {num_batches * (delay + 5):.0f}s")
                print("\nRun without --dry-run to populate embeddings")

        await db_manager.close()
        return

    start_time = time.time()

    event_bus = EventBus()
    logger = Logger("memory-log-embeddings")

    embedding_config = ProviderConfig(
        provider_name=service_config.embedding.provider_name,
        model_name=service_config.embedding.model_name,
        api_key=service_config.embedding.api_key,
        timeout_seconds=service_config.embedding.timeout_seconds,
        max_retries=service_config.embedding.max_retries,
    )

    provider = GoogleEmbeddingProvider(embedding_config)
    embedding_service = EmbeddingService(
        event_bus=event_bus,
        logger=logger,
        provider=provider,
        cache=EmbeddingCache(),
        cache_enabled=False,
    )

    print("Services initialized")
    print(f"Embedding model: {embedding_config.model_name}")
    print(f"Batch size: {batch_size}")
    print(f"Delay between batches: {delay}s")
    print()

    batch_num = 0
    total_processed_this_run = 0
    total_errors_this_run = 0
    total_skipped_this_run = 0

    try:
        while True:
            if limit and total_processed_this_run >= limit:
                print(f"\nReached limit of {limit} memory logs. Stopping.")
                break

            if limit:
                remaining_to_process = limit - total_processed_this_run
                current_batch_size = min(batch_size, remaining_to_process)
            else:
                current_batch_size = batch_size

            async with db_manager.session_factory() as session:
                result = await session.execute(
                    select(MemoryLog)
                    .where(MemoryLog.embedding.is_(None))
                    .order_by(MemoryLog.created_at)
                    .offset(current_offset)
                    .limit(current_batch_size)
                )
                memory_logs = list(result.scalars().all())

            if not memory_logs:
                print("\nNo more memory logs to process.")
                break

            batch_num += 1
            batch_count = len(memory_logs)

            print(f"Batch {batch_num} (offset {current_offset}, {batch_count} records):")
            print("-" * 70)

            texts: List[str] = []
            valid_logs: List[MemoryLog] = []

            for log in memory_logs:
                try:
                    text = prepare_memory_log_text(log)

                    if not text or text == "[]":
                        print(f"  Skipped {log.id[:8]}... (no text content)")
                        total_skipped_this_run += 1
                        continue

                    text_size = len(text.encode("utf-8"))
                    if text_size > MAX_TEXT_SIZE_BYTES:
                        print(f"  Skipped {log.id[:8]}... (too large: {text_size:,} bytes, limit: {MAX_TEXT_SIZE_BYTES:,})")
                        progress.add_oversized_id(log.id)
                        total_skipped_this_run += 1
                        continue

                    texts.append(text)
                    valid_logs.append(log)
                except Exception as e:
                    print(f"  Error preparing {log.id}: {e}")
                    progress.add_failed_id(log.id)
                    total_errors_this_run += 1

            if not texts:
                print("  No valid texts in this batch. Moving to next batch.")
                current_offset += batch_count
                progress.update(offset=current_offset)
                continue

            print(f"  Prepared {len(texts)} texts")

            max_retries = 3
            retry_delay = 2.0

            for attempt in range(max_retries):
                try:
                    print(f"  Generating embeddings (attempt {attempt + 1}/{max_retries})...")
                    result = await embedding_service.generate_embeddings_batch(texts)
                    print(f"  Generated {len(result.embeddings)} embeddings in {result.processing_time_seconds:.2f}s")
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)
                        print(f"  API error: {e}")
                        print(f"  Waiting {wait_time:.0f}s before retry...")
                        await asyncio.sleep(wait_time)
                    else:
                        print(f"  Failed after {max_retries} attempts: {e}")
                        print("  Progress saved. Run with --resume to continue.")
                        progress.update(offset=current_offset)
                        raise

            print("  Updating PostgreSQL...")
            batch_success = 0
            batch_errors = 0

            for i, log in enumerate(valid_logs):
                try:
                    embedding_vector = result.embeddings[i].embedding
                    success = await update_memory_log_embedding(db_manager, log.id, embedding_vector)
                    if success:
                        print(f"    Updated {log.id[:8]}... ({len(texts[i])} chars | {len(embedding_vector)} dims)")
                        batch_success += 1
                    else:
                        progress.add_failed_id(log.id)
                        batch_errors += 1
                except Exception as e:
                    print(f"    Failed to update {log.id}: {e}")
                    progress.add_failed_id(log.id)
                    batch_errors += 1

            total_processed_this_run += batch_success
            total_errors_this_run += batch_errors

            progress.update(
                processed=batch_success,
                errors=batch_errors,
                skipped=total_skipped_this_run - progress.data["total_skipped"],
                offset=current_offset + batch_count,
            )

            current_offset += batch_count

            print(f"  Batch complete: {batch_success} success, {batch_errors} errors")
            print()

            if delay > 0 and memory_logs:
                print(f"  Waiting {delay}s before next batch...")
                await asyncio.sleep(delay)
                print()

    except KeyboardInterrupt:
        print("\nInterrupted by user")
        print(f"Progress saved at offset {current_offset}")
        print("Run with --resume to continue from this point")
    except Exception as e:
        print(f"\nFatal error: {e}")
        print(f"Progress saved at offset {current_offset}")
        print("Run with --resume to continue from this point")
    finally:
        await embedding_service.close()
        await db_manager.close()

    elapsed_time = time.time() - start_time

    print()
    print("=" * 70)
    print("Summary")
    print("-" * 70)
    print(f"This run:")
    print(f"  Processed: {total_processed_this_run}")
    print(f"  Errors: {total_errors_this_run}")
    print(f"  Skipped: {total_skipped_this_run}")
    print(f"  Time: {elapsed_time:.1f}s")
    print()
    print("Overall progress:")
    print(f"  Total processed: {progress.data['total_processed']}")
    print(f"  Total errors: {progress.data['total_errors']}")
    print(f"  Total skipped: {progress.data['total_skipped']}")
    print(f"  Current offset: {progress.data['last_offset']}")
    print(f"  Failed IDs: {len(progress.data['failed_ids'])}")
    print(f"  Oversized IDs: {len(progress.data['oversized_ids'])}")
    print()

    if progress.data["failed_ids"]:
        print("Failed memory log IDs (first 10):")
        for fid in progress.data["failed_ids"][:10]:
            print(f"  - {fid}")
        if len(progress.data["failed_ids"]) > 10:
            print(f"  ... and {len(progress.data['failed_ids']) - 10} more")
        print()

    if progress.data["oversized_ids"]:
        print(f"Oversized memory log IDs (exceeded {MAX_TEXT_SIZE_BYTES:,} bytes, first 10):")
        for oid in progress.data["oversized_ids"][:10]:
            print(f"  - {oid}")
        if len(progress.data["oversized_ids"]) > 10:
            print(f"  ... and {len(progress.data['oversized_ids']) - 10} more")
        print()


def main():
    args = parse_args()
    asyncio.run(
        populate_embeddings(
            dry_run=args.dry_run,
            batch_size=args.batch_size,
            limit=args.limit,
            resume=args.resume,
            start_from=args.start_from,
            delay=args.delay,
            reset_progress=args.reset_progress,
        )
    )


if __name__ == "__main__":
    main()


"""
Populate embeddings for conversations that don't have them yet.

This script:
1. Queries conversations with NULL embeddings from PostgreSQL
2. Extracts text from conversation messages (user + assistant)
3. Generates embeddings using EmbeddingService
4. Updates PostgreSQL with the embeddings
5. Supports resumability via progress file for API rate limit handling

Key features:
- Batch processing with configurable batch size
- Progress tracking with resumable offset
- Rate limit handling with exponential backoff
- Dry-run mode for testing
- Progress file for continuing after interruption

Usage:
    python scripts/populate_conversation_embeddings.py --dry-run          # Preview
    python scripts/populate_conversation_embeddings.py                    # Run
    python scripts/populate_conversation_embeddings.py --resume           # Continue from last
    python scripts/populate_conversation_embeddings.py --batch-size 25    # Smaller batches
    python scripts/populate_conversation_embeddings.py --limit 100        # Process only 100
"""

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path
from typing import List, Dict, Any, Optional
import re
from datetime import datetime

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

from sqlalchemy import text as sql_text
from src.api.bootstrap.config import load_app_config, load_service_config
from src.database import DatabaseManager
from src.database.repositories.conversation.repository import ConversationRepository
from src.database.models import Conversation
from src.modules.core import EventBus, Logger
from src.modules.embeddings import (
    EmbeddingService,
    GoogleEmbeddingProvider,
    ProviderConfig,
    EmbeddingCache,
)


BATCH_SIZE = 50
PROGRESS_FILE = Path(__file__).parent / "conversation_embedding_progress.json"
DELAY_BETWEEN_BATCHES = 1.0  # seconds
MAX_TEXT_SIZE_BYTES = 30000  # 30KB safety margin (Google API limit is 36KB)


class ProgressTracker:
    """Track progress for resumability."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        """Load progress from file."""
        if self.file_path.exists():
            try:
                with open(self.file_path, 'r') as f:
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
            "oversized_ids": []
        }

    def save(self):
        """Save progress to file."""
        try:
            self.data["last_run"] = datetime.utcnow().isoformat()
            with open(self.file_path, 'w') as f:
                json.dump(self.data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not save progress file: {e}")

    def update(self, processed: int = 0, errors: int = 0, skipped: int = 0, offset: int = None):
        """Update progress counters."""
        self.data["total_processed"] += processed
        self.data["total_errors"] += errors
        self.data["total_skipped"] += skipped
        if offset is not None:
            self.data["last_offset"] = offset
        self.save()

    def add_failed_id(self, conversation_id: str):
        """Track failed conversation ID."""
        if conversation_id not in self.data["failed_ids"]:
            self.data["failed_ids"].append(conversation_id)
        self.save()

    def add_oversized_id(self, conversation_id: str):
        """Track oversized conversation ID."""
        if "oversized_ids" not in self.data:
            self.data["oversized_ids"] = []
        if conversation_id not in self.data["oversized_ids"]:
            self.data["oversized_ids"].append(conversation_id)
        self.save()

    @property
    def offset(self) -> int:
        """Get current offset."""
        return self.data["last_offset"]

    def reset(self):
        """Reset progress."""
        self.data = {
            "last_offset": 0,
            "total_processed": 0,
            "total_errors": 0,
            "total_skipped": 0,
            "last_run": None,
            "failed_ids": [],
            "oversized_ids": []
        }
        self.save()


def parse_args():
    parser = argparse.ArgumentParser(description="Populate conversation embeddings")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be processed without making changes"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=BATCH_SIZE,
        help=f"Number of conversations to process at once (default: {BATCH_SIZE})"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Maximum total conversations to process (default: all)"
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help="Resume from last saved offset in progress file"
    )
    parser.add_argument(
        "--start-from",
        type=int,
        default=None,
        help="Start from specific offset (overrides --resume)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=DELAY_BETWEEN_BATCHES,
        help=f"Delay between batches in seconds (default: {DELAY_BETWEEN_BATCHES})"
    )
    parser.add_argument(
        "--reset-progress",
        action="store_true",
        help="Reset progress file before starting"
    )
    return parser.parse_args()


def _extract_message_text(msg: Any) -> str:
    """Return plain text from a message dict with flexible schemas."""
    if not isinstance(msg, dict):
        return ""

    # Common fields
    if isinstance(msg.get("text"), str):
        return msg["text"]

    if isinstance(msg.get("content"), str):
        return msg["content"]

    if isinstance(msg.get("content"), list):
        parts = msg["content"]
        return " ".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in parts
        ).strip()

    if isinstance(msg.get("parts"), list):
        return " ".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in msg["parts"]
        ).strip()

    return ""


def prepare_conversation_text(
    conversation: Conversation
) -> str:
    """
    Normalize conversation turns into paired user/assistant objects for embedding.

    Output is a JSON list of:
    {
      "user": "message in natural language here.",
      "assistant": "response in natural language here.",
      "metadata": {
        "timestamp": "...",
        "conversation_id": "...",
        "source": "conversation"
      }
    }
    """
    turns: List[Dict[str, Any]] = []

    raw = conversation.raw_data or {}
    candidates = []

    if isinstance(raw, list):
        candidates = raw
    elif isinstance(raw, dict):
        if isinstance(raw.get("conversation"), list):
            candidates = raw["conversation"]
        elif isinstance(raw.get("messages"), list):
            candidates = raw["messages"]
        elif isinstance(raw.get("memory_log"), dict):
            mem_log = raw["memory_log"]
            if isinstance(mem_log.get("conversation"), list):
                candidates = mem_log["conversation"]

    pending_user: Optional[str] = None
    for msg in candidates:
        if not isinstance(msg, dict):
            continue
        role = msg.get("role", "").strip()
        text = _strip_memory_blocks(_extract_message_text(msg)).strip()
        if not role or not text:
            continue

        timestamp = (
            msg.get("timestamp")
            or msg.get("created_at")
            or (conversation.created_at.isoformat() if conversation.created_at else None)
        )

        metadata = {
            "timestamp": timestamp,
            "conversation_id": conversation.conversation_id,
            "source": "conversation",
        }

        if role == "user":
            pending_user = text
        elif role == "assistant":
            if pending_user is not None:
                turns.append(
                    {
                        "user": pending_user,
                        "assistant": text,
                        "metadata": metadata,
                    }
                )
                pending_user = None
            else:
                turns.append(
                    {
                        "user": "",
                        "assistant": text,
                        "metadata": metadata,
                    }
                )

    # Capture trailing user message without assistant reply
    if pending_user:
        turns.append(
            {
                "user": pending_user,
                "assistant": "",
                "metadata": {
                    "timestamp": conversation.created_at.isoformat() if conversation.created_at else None,
                    "conversation_id": conversation.conversation_id,
                    "source": "conversation",
                },
            }
        )

    return json.dumps(turns, ensure_ascii=False, sort_keys=True)


def _strip_memory_blocks(text: str) -> str:
    """
    Remove [semantix-memory-block] ... [semantix-end-memory-block] content.
    """
    if not text:
        return ""
    return re.sub(
        r"\[semantix-memory-block\].*?\[semantix-end-memory-block\]",
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )


async def update_conversation_embedding(
    db_manager: DatabaseManager,
    conversation_id: str,
    embedding: List[float]
) -> bool:
    """
    Update conversation with embedding using raw SQL.

    Args:
        db_manager: Database manager instance
        conversation_id: Conversation ID to update
        embedding: 768-dimensional embedding vector

    Returns:
        True if successful, False otherwise
    """
    try:
        async with db_manager.session_factory() as session:
            # Convert list to pgvector format string
            vector_str = f"[{','.join(map(str, embedding))}]"

            # Use raw SQL for pgvector compatibility
            sql = sql_text(f"""
                UPDATE conversations
                SET embedding = '{vector_str}'::vector
                WHERE id = '{conversation_id}'
            """)

            await session.execute(sql)
            await session.commit()
            return True
    except Exception as e:
        print(f"    ✗ Database update failed: {e}")
        return False


async def populate_embeddings(
    dry_run: bool,
    batch_size: int,
    limit: Optional[int],
    resume: bool,
    start_from: Optional[int],
    delay: float,
    reset_progress: bool
):
    """Main function to populate conversation embeddings."""

    print("\nConversation Embeddings Population Script")
    print("=" * 70)
    print()

    # Initialize progress tracker
    progress = ProgressTracker(PROGRESS_FILE)

    if reset_progress:
        print("Resetting progress file...")
        progress.reset()
        print()

    # Determine starting offset
    # Note: We always use offset 0 because the query filters by "embedding IS NULL"
    # which automatically excludes already-processed conversations
    if start_from is not None:
        current_offset = start_from
        print(f"Starting from offset: {current_offset} (manual override)")
    elif resume:
        # Always start from 0 when resuming - WHERE clause handles filtering
        current_offset = 0
        print(f"Resuming (offset reset to 0, query filters by embedding IS NULL)")
        if progress.data["last_run"]:
            print(f"Last run: {progress.data['last_run']}")
            print(f"Previously processed: {progress.data['total_processed']}")
    else:
        current_offset = 0
        print("Starting from beginning (offset: 0)")

    print()

    if dry_run:
        print("Mode: DRY RUN (no changes will be made)")
    else:
        print("Mode: LIVE (will generate and update embeddings)")
    print()

    # Load configuration
    load_dotenv()
    app_config = load_app_config()
    service_config = load_service_config()

    # Check if embedding service is available
    if not service_config.embedding.is_available:
        print("Error: Embedding service not available")
        print("Make sure GOOGLE_API_KEY is set in your .env file")
        sys.exit(1)

    # Initialize database
    db_manager = DatabaseManager(app_config.database_url)

    # Get total count of conversations without embeddings
    async with db_manager.session_factory() as session:
        repo = ConversationRepository(session)
        total_without_embeddings = await repo.count_without_embeddings()

    print(f"Total conversations without embeddings: {total_without_embeddings}")

    if total_without_embeddings == 0:
        print("\nNo conversations need embeddings. Exiting.")
        await db_manager.close()
        return

    # Calculate how many to process
    remaining = total_without_embeddings - current_offset
    if limit:
        to_process = min(remaining, limit)
        print(f"Will process: {to_process} conversations (limit: {limit})")
    else:
        to_process = remaining
        print(f"Will process: {to_process} conversations (all remaining)")

    print()

    if dry_run:
        # Dry run - show samples
        async with db_manager.session_factory() as session:
            repo = ConversationRepository(session)
            sample_conversations = await repo.get_without_embeddings(
                limit=min(5, to_process),
                offset=current_offset
            )

            if sample_conversations:
                print("Sample conversations:")
                for i, conv in enumerate(sample_conversations, 1):
                    text = prepare_conversation_text(conv)
                    msg_count = len(conv.raw_data.get('conversation', []))
                    print(f"\n{i}. Conversation ID: {conv.id}")
                    print(f"   Model: {conv.model}")
                    print(f"   User: {conv.user_id}")
                    print(f"   Session: {conv.session_id}")
                    print(f"   Messages: {msg_count}")
                    print(f"   Text length: {len(text)} chars")
                    print(f"   Created: {conv.created_at}")

                num_batches = (to_process + batch_size - 1) // batch_size
                print(f"\nWould process in {num_batches} batch(es) of {batch_size}")
                print(f"With {delay}s delay between batches")
                print(f"Estimated time: {num_batches * (delay + 5):.0f}s")
                print()
                print("Run without --dry-run to populate embeddings")

        await db_manager.close()
        return

    # Live mode - generate and update embeddings
    start_time = time.time()

    # Initialize services
    event_bus = EventBus()
    logger = Logger("conversation-embeddings")

    # Create embedding provider config
    embedding_config = ProviderConfig(
        provider_name=service_config.embedding.provider_name,
        model_name=service_config.embedding.model_name,
        api_key=service_config.embedding.api_key,
        timeout_seconds=service_config.embedding.timeout_seconds,
        max_retries=service_config.embedding.max_retries
    )

    # Create provider and service
    provider = GoogleEmbeddingProvider(embedding_config)
    embedding_service = EmbeddingService(
        event_bus=event_bus,
        logger=logger,
        provider=provider,
        cache=EmbeddingCache(),
        cache_enabled=False  # Disable cache for batch processing
    )

    print("Services initialized")
    print(f"Embedding model: {embedding_config.model_name}")
    print(f"Batch size: {batch_size}")
    print(f"Delay between batches: {delay}s")
    print("Text preparation: raw conversation turns (compression disabled)")
    print()

    batch_num = 0
    total_processed_this_run = 0
    total_errors_this_run = 0
    total_skipped_this_run = 0

    try:
        while True:
            # Check if we've hit the limit
            if limit and total_processed_this_run >= limit:
                print(f"\nReached limit of {limit} conversations. Stopping.")
                break

            # Calculate batch size for this iteration
            if limit:
                remaining_to_process = limit - total_processed_this_run
                current_batch_size = min(batch_size, remaining_to_process)
            else:
                current_batch_size = batch_size

            # Get next batch
            async with db_manager.session_factory() as session:
                repo = ConversationRepository(session)
                conversations = await repo.get_without_embeddings(
                    limit=current_batch_size,
                    offset=current_offset
                )

            if not conversations:
                print("\nNo more conversations to process.")
                break

            batch_num += 1
            batch_count = len(conversations)

            print(f"Batch {batch_num} (offset {current_offset}, {batch_count} records):")
            print("-" * 70)

            # Prepare texts for embedding
            print("  Preparing conversation texts...")
            texts = []
            valid_conversations = []

            for conv in conversations:
                try:
                    text = prepare_conversation_text(conv)

                    if not text or text == "[]":
                        print(f"  ⊘ Skipped {conv.id[:8]}... (no text content)")
                        total_skipped_this_run += 1
                        continue

                    # Check text size to avoid API payload limits
                    text_size = len(text.encode('utf-8'))
                    if text_size > MAX_TEXT_SIZE_BYTES:
                        print(f"  ⊘ Skipped {conv.id[:8]}... (too large: {text_size:,} bytes, limit: {MAX_TEXT_SIZE_BYTES:,})")
                        progress.add_oversized_id(conv.id)
                        total_skipped_this_run += 1
                        continue

                    texts.append(text)
                    valid_conversations.append(conv)

                except Exception as e:
                    print(f"  ✗ Error preparing {conv.id}: {e}")
                    progress.add_failed_id(conv.id)
                    total_errors_this_run += 1

            if not texts:
                print(f"  No valid texts in this batch. Moving to next batch.")
                current_offset += batch_count
                progress.update(offset=current_offset)
                continue

            print(f"  Prepared {len(texts)} texts")

            # Generate embeddings with retry logic
            max_retries = 3
            retry_delay = 2.0

            for attempt in range(max_retries):
                try:
                    print(f"  Generating embeddings (attempt {attempt + 1}/{max_retries})...")
                    result = await embedding_service.generate_embeddings_batch(texts)

                    print(f"  ✓ Generated {len(result.embeddings)} embeddings in {result.processing_time_seconds:.2f}s")
                    break
                except Exception as e:
                    if attempt < max_retries - 1:
                        wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                        print(f"  ⚠ API error: {e}")
                        print(f"  ⏳ Waiting {wait_time:.0f}s before retry...")
                        await asyncio.sleep(wait_time)
                    else:
                        print(f"  ✗ Failed after {max_retries} attempts: {e}")
                        print(f"  💾 Progress saved. Run with --resume to continue.")
                        progress.update(offset=current_offset)
                        raise

            # Update database
            print("  Updating PostgreSQL...")
            batch_success = 0
            batch_errors = 0

            for i, conv in enumerate(valid_conversations):
                try:
                    embedding_vector = result.embeddings[i].embedding

                    success = await update_conversation_embedding(
                        db_manager,
                        conv.id,
                        embedding_vector
                    )

                    if success:
                        print(f"    ✓ {conv.id[:8]}... ({len(texts[i])} chars → {len(embedding_vector)} dims)")
                        batch_success += 1
                    else:
                        progress.add_failed_id(conv.id)
                        batch_errors += 1
                except Exception as e:
                    print(f"    ✗ Failed to update {conv.id}: {e}")
                    progress.add_failed_id(conv.id)
                    batch_errors += 1

            total_processed_this_run += batch_success
            total_errors_this_run += batch_errors

            # Update progress (no offset tracking needed - WHERE clause filters)
            progress.update(
                processed=batch_success,
                errors=batch_errors,
                skipped=total_skipped_this_run - progress.data["total_skipped"],
                offset=0  # Always 0 since we query WHERE embedding IS NULL
            )

            print(f"  Batch complete: {batch_success} success, {batch_errors} errors")
            print()

            # Delay between batches to avoid rate limits
            if delay > 0 and conversations:  # Only delay if there might be more
                print(f"  ⏳ Waiting {delay}s before next batch...")
                await asyncio.sleep(delay)
                print()

    except KeyboardInterrupt:
        print("\n\n⚠ Interrupted by user")
        print(f"💾 Progress saved at offset {current_offset}")
        print("Run with --resume to continue from this point")
    except Exception as e:
        print(f"\n\n✗ Fatal error: {e}")
        print(f"💾 Progress saved at offset {current_offset}")
        print("Run with --resume to continue from this point")
    finally:
        # Cleanup
        await embedding_service.close()
        await db_manager.close()

    # Summary
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
    print(f"Overall progress:")
    print(f"  Total processed: {progress.data['total_processed']}")
    print(f"  Total errors: {progress.data['total_errors']}")
    print(f"  Total skipped: {progress.data['total_skipped']}")
    print(f"  Current offset: {progress.data['last_offset']}")
    print(f"  Failed IDs: {len(progress.data['failed_ids'])}")
    print(f"  Oversized IDs: {len(progress.data.get('oversized_ids', []))}")
    print()

    if progress.data['failed_ids']:
        print(f"Failed conversation IDs (first 10):")
        for fid in progress.data['failed_ids'][:10]:
            print(f"  - {fid}")
        if len(progress.data['failed_ids']) > 10:
            print(f"  ... and {len(progress.data['failed_ids']) - 10} more")
        print()

    if progress.data.get('oversized_ids'):
        print(f"Oversized conversation IDs (exceeded {MAX_TEXT_SIZE_BYTES:,} bytes, first 10):")
        for oid in progress.data['oversized_ids'][:10]:
            print(f"  - {oid}")
        if len(progress.data['oversized_ids']) > 10:
            print(f"  ... and {len(progress.data['oversized_ids']) - 10} more")
        print()
        print("Note: Oversized conversations need manual truncation before embedding.")


def main():
    args = parse_args()
    asyncio.run(populate_embeddings(
        dry_run=args.dry_run,
        batch_size=args.batch_size,
        limit=args.limit,
        resume=args.resume,
        start_from=args.start_from,
        delay=args.delay,
        reset_progress=args.reset_progress
    ))


if __name__ == "__main__":
    main()

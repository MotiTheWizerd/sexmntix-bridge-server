"""
Generate embeddings for mental notes that don't have them yet.

This is a simple one-time batch script that:
1. Queries mental notes with NULL embeddings
2. Generates embeddings using EmbeddingService
3. Updates the database directly

Usage:
    python scripts/generate_mental_note_embeddings.py --dry-run  # Preview without changes
    python scripts/generate_mental_note_embeddings.py            # Generate embeddings
"""

import argparse
import asyncio
import json
import sys
import time
import numpy as np
from pathlib import Path
from typing import List

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
from src.database.repositories.mental_note_repository import MentalNoteRepository
from src.database.models import MentalNote
from src.modules.core import EventBus, Logger
from src.modules.embeddings import (
    EmbeddingService,
    GoogleEmbeddingProvider,
    ProviderConfig,
    EmbeddingCache,
)


BATCH_SIZE = 70


def parse_args():
    parser = argparse.ArgumentParser(description="Generate embeddings for mental notes")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview what would be processed without making changes"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=BATCH_SIZE,
        help=f"Number of records to process at once (default: {BATCH_SIZE})"
    )
    return parser.parse_args()


def prepare_text_for_embedding(mental_note: MentalNote) -> str:
    """
    Convert mental note raw_data to text for embedding.

    Serializes the entire raw_data JSONB field as a JSON string.
    This preserves all context: session info, entry types, content, metadata.

    Args:
        mental_note: MentalNote instance with raw_data

    Returns:
        JSON string representation of the mental note
    """
    return json.dumps(mental_note.raw_data, sort_keys=True, default=str)


async def generate_embeddings(dry_run: bool, batch_size: int):
    """Generate embeddings for mental notes without them."""

    print("\nMental Notes Embedding Generator")
    print("=" * 60)
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

    if dry_run:
        # Dry run - just count records
        async with db_manager.session_factory() as session:
            repo = MentalNoteRepository(session)
            mental_notes = await repo.get_without_embeddings(limit=1000)

            print(f"Found: {len(mental_notes)} mental note(s) without embeddings")
            print()

            if mental_notes:
                print("Sample records:")
                for i, note in enumerate(mental_notes[:5], 1):
                    text = prepare_text_for_embedding(note)
                    entries_count = len(note.raw_data.get("entries", []))
                    print(f"\n{i}. Mental Note ID: {note.id}")
                    print(f"   Session: {note.session_id}")
                    print(f"   Entries: {entries_count}")
                    print(f"   Text length: {len(text)} chars")

                if len(mental_notes) > 5:
                    print(f"\n... and {len(mental_notes) - 5} more")

                print()
                print(f"Would process in {(len(mental_notes) + batch_size - 1) // batch_size} batch(es)")
                print()
                print("Run without --dry-run to generate embeddings")

        await db_manager.close()
        return

    # Live mode - generate embeddings
    start_time = time.time()

    # Initialize services
    event_bus = EventBus()
    logger = Logger("batch-embeddings")

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
    print()

    total_processed = 0
    total_errors = 0
    batch_num = 0

    async with db_manager.session_factory() as session:
        repo = MentalNoteRepository(session)

        # Process in batches
        while True:
            try:
                # Rollback any pending transaction (in case of previous error)
                await session.rollback()

                # Get next batch
                mental_notes = await repo.get_without_embeddings(limit=batch_size)

                if not mental_notes:
                    break

                batch_num += 1
                batch_count = len(mental_notes)

                print(f"Batch {batch_num} ({batch_count} records):")
                print("-" * 60)

                # Prepare texts for embedding
                print("  Preparing texts...")
                texts = [prepare_text_for_embedding(note) for note in mental_notes]

                # Generate embeddings
                print("  Generating embeddings...")
                result = await embedding_service.generate_embeddings_batch(texts)

                print(f"  Generated {len(result.embeddings)} embeddings in {result.processing_time_seconds:.2f}s")

                # Update database using raw SQL (pgvector requires special handling)
                print("  Updating database...")
                for i, mental_note in enumerate(mental_notes):
                    embedding_vector = result.embeddings[i].embedding

                    # Debug: check the type
                    print(f"  Debug: embedding type = {type(embedding_vector)}, length = {len(embedding_vector)}")
                    print(f"  Debug: first 3 values = {embedding_vector[:3]}")

                    # Use raw SQL with pgvector's array format
                    async with db_manager.session_factory() as update_session:
                        # Convert list to pgvector format string
                        vector_str = f"[{','.join(map(str, embedding_vector))}]"

                        # Use direct SQL with proper quoting
                        sql = sql_text(f"""
                            UPDATE mental_notes
                            SET embedding = '{vector_str}'::vector
                            WHERE id = '{mental_note.id}'
                        """)

                        await update_session.execute(sql)
                        await update_session.commit()

                    print(f"  ✓ Updated {mental_note.id}")
                    print(f"    Text: {len(texts[i])} chars, Embedding: {len(embedding_vector)} dims")

                total_processed += batch_count
                print()

            except Exception as e:
                print(f"  ✗ Batch failed: {e}")
                await session.rollback()
                total_errors += batch_count if 'batch_count' in locals() else 1
                print()
                break  # Stop on error for debugging

    # Cleanup
    await embedding_service.close()
    await db_manager.close()

    # Summary
    elapsed_time = time.time() - start_time

    print()
    print("=" * 60)
    print("Summary")
    print("-" * 60)
    print(f"Total processed: {total_processed}")
    print(f"Total errors: {total_errors}")
    print(f"Time: {elapsed_time:.1f}s")
    print()


def main():
    args = parse_args()
    asyncio.run(generate_embeddings(
        dry_run=args.dry_run,
        batch_size=args.batch_size
    ))


if __name__ == "__main__":
    main()

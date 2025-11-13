"""
Test script for event-driven memory log storage.

Tests the flow:
1. Scan .semantix/memories/delta/ for JSON files
2. Process each file: emit memory_log.stored event
3. Generate embeddings and store in ChromaDB
4. Move processed files to .semantix/memories/processed/
5. Move failed files to .semantix/memories/errors/
"""

import asyncio
import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

# Set up paths
os.environ.setdefault("CHROMADB_PATH", "./data/chromadb")
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/semantic_bridge")

from src.modules.core import EventBus, Logger
from src.modules.embeddings import (
    EmbeddingService,
    GoogleEmbeddingProvider,
    ProviderConfig,
    EmbeddingCache,
)
from src.infrastructure.chromadb.client import ChromaDBClient
from src.infrastructure.chromadb.repository import VectorRepository
from src.modules.vector_storage import VectorStorageService
from src.events.internal_handlers import MemoryLogStorageHandlers
from src.api.dependencies.database import get_db_session

# Configuration
USER_ID = "9b1cdb78-df73-4ae4-8f80-41be3c0fdc1e"
PROJECT_ID = "152ec016-2c28-4609-ab1b-dff831b3ba96"
DELTA_DIR = Path(".semantix/memories/delta")
PROCESSED_DIR = Path(".semantix/memories/processed")
ERRORS_DIR = Path(".semantix/memories/errors")


async def process_memory_file(
    file_path: Path,
    event_bus: EventBus,
    logger: Logger,
    memory_id_counter: int
) -> tuple[bool, str]:
    """
    Process a single memory JSON file.

    Returns:
        (success: bool, error_message: str)
    """
    try:
        # Read and parse JSON
        with open(file_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)

        # Generate unique memory_log_id from counter
        memory_log_id = memory_id_counter

        # Extract task name for logging
        task_name = raw_data.get("task", file_path.stem)

        logger.info(f"Processing {file_path.name} (ID: {memory_log_id}, Task: {task_name})")

        # Construct event data
        event_data = {
            "memory_log_id": memory_log_id,
            "task": task_name,
            "agent": raw_data.get("agent", "unknown"),
            "date": raw_data.get("date", datetime.now().isoformat()),
            "raw_data": raw_data,  # Entire JSON becomes raw_data for embedding
            "user_id": USER_ID,
            "project_id": PROJECT_ID
        }

        # Emit event and wait for processing
        await event_bus.publish_async("memory_log.stored", event_data)

        # Brief wait for async completion
        await asyncio.sleep(1)

        return True, ""

    except json.JSONDecodeError as e:
        error_msg = f"Invalid JSON: {e}"
        logger.error(f"Failed to parse {file_path.name}: {error_msg}")
        return False, error_msg
    except Exception as e:
        error_msg = f"Processing error: {e}"
        logger.error(f"Failed to process {file_path.name}: {error_msg}")
        return False, error_msg


async def main():
    print("=" * 80)
    print("Batch Processing Memory Logs from Delta Directory")
    print("=" * 80)

    # Ensure directories exist
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    ERRORS_DIR.mkdir(parents=True, exist_ok=True)

    # Initialize core services
    event_bus = EventBus()
    logger = Logger(name="test_event_flow")

    # Initialize embedding service
    google_api_key = os.getenv("GOOGLE_API_KEY")
    if not google_api_key:
        print("\nERROR: GOOGLE_API_KEY not found in environment")
        return

    embedding_config = ProviderConfig(
        provider_name="google",
        model_name="models/text-embedding-004",
        api_key=google_api_key,
        timeout_seconds=30.0,
        max_retries=3
    )

    embedding_provider = GoogleEmbeddingProvider(embedding_config)
    embedding_cache = EmbeddingCache(max_size=1000, ttl_hours=24)

    embedding_service = EmbeddingService(
        event_bus=event_bus,
        logger=logger,
        provider=embedding_provider,
        cache=embedding_cache,
        cache_enabled=True
    )

    # Initialize event handlers (with per-project isolation)
    # Handlers will create VectorStorageService dynamically for each event
    handlers = MemoryLogStorageHandlers(
        db_session_factory=get_db_session,
        embedding_service=embedding_service,
        event_bus=event_bus,
        logger=logger
    )

    # Register event handler
    event_bus.subscribe("memory_log.stored", handlers.handle_memory_log_stored)

    print("\nServices initialized successfully")
    print(f"- Event bus: {event_bus}")
    print(f"- User ID: {USER_ID}")
    print(f"- Project ID: {PROJECT_ID}")
    print(f"- Delta directory: {DELTA_DIR}")
    print(f"- Event handler registered for: memory_log.stored")

    # Find all JSON files in delta directory
    print(f"\n{'=' * 80}")
    print("Scanning for memory files...")
    print(f"{'=' * 80}")

    if not DELTA_DIR.exists():
        print(f"\nERROR: Delta directory not found: {DELTA_DIR}")
        return

    json_files = list(DELTA_DIR.glob("*.json"))

    if not json_files:
        print(f"\nNo JSON files found in {DELTA_DIR}")
        return

    print(f"\nFound {len(json_files)} file(s) to process:")
    for i, file_path in enumerate(json_files, 1):
        print(f"  {i}. {file_path.name}")

    # Process each file
    print(f"\n{'=' * 80}")
    print("Processing files...")
    print(f"{'=' * 80}\n")

    stats = {
        "total": len(json_files),
        "succeeded": 0,
        "failed": 0
    }

    for i, file_path in enumerate(json_files, 1):
        memory_id = i  # Use sequential ID

        print(f"[{i}/{len(json_files)}] Processing {file_path.name}...")

        success, error_msg = await process_memory_file(
            file_path=file_path,
            event_bus=event_bus,
            logger=logger,
            memory_id_counter=memory_id
        )

        if success:
            # Move to processed directory
            dest_path = PROCESSED_DIR / file_path.name
            shutil.move(str(file_path), str(dest_path))
            stats["succeeded"] += 1
            print(f"  [SUCCESS] Moved to {PROCESSED_DIR.name}/")
        else:
            # Move to errors directory
            dest_path = ERRORS_DIR / file_path.name
            shutil.move(str(file_path), str(dest_path))
            stats["failed"] += 1
            print(f"  [FAILED] {error_msg} -> moved to {ERRORS_DIR.name}/")

        print()

    # Summary statistics
    print(f"{'=' * 80}")
    print("Processing Summary")
    print(f"{'=' * 80}")
    print(f"  Total files: {stats['total']}")
    print(f"  Succeeded: {stats['succeeded']}")
    print(f"  Failed: {stats['failed']}")

    # Check cache stats
    cache_stats = embedding_service.get_cache_stats()
    print(f"\nCache Statistics:")
    print(f"  - Total requests: {cache_stats['total_requests']}")
    print(f"  - Cache hits: {cache_stats['hit_count']}")
    print(f"  - Cache misses: {cache_stats['miss_count']}")
    print(f"  - Hit rate: {cache_stats['hit_rate_percent']:.1f}%")

    # Verify storage - create isolated ChromaDB client for verification
    print(f"\nVerifying vector storage...")
    from src.api.dependencies.vector_storage import create_vector_storage_service

    verification_service = create_vector_storage_service(
        user_id=USER_ID,
        project_id=PROJECT_ID,
        embedding_service=embedding_service,
        event_bus=event_bus,
        logger=logger
    )

    count = await verification_service.count_memories(USER_ID, PROJECT_ID)
    print(f"  - Vectors stored for user/project: {count}")

    # Search test
    if stats["succeeded"] > 0:
        print(f"\nTesting semantic search...")
        results = await verification_service.search_similar_memories(
            query="event-driven architecture and ChromaDB integration",
            user_id=USER_ID,
            project_id=PROJECT_ID,
            limit=5
        )

        print(f"  - Found {len(results)} similar memories:")
        for i, result in enumerate(results, 1):
            # Extract task name from document
            task_name = result['document'].get('task', 'Unknown') if isinstance(result['document'], dict) else 'N/A'
            print(f"    {i}. Similarity: {result['similarity']:.2%} - Task: {task_name}")

    # Cleanup
    await embedding_service.close()
    print(f"\n{'=' * 80}")
    print("Batch processing completed!")
    print(f"{'=' * 80}")


if __name__ == "__main__":
    asyncio.run(main())

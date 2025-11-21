# Next Session: Generate Embeddings for Migrated Data

## Context

We successfully migrated memory logs and mental notes from JSON files to PostgreSQL:
- ✅ **487 memory logs** migrated to `memory_logs` table
- ✅ **1 mental note session** migrated to `mental_notes` table

**Problem:** These records were migrated **directly to the database**, bypassing the API routes, so the event handlers never fired. Result: All records have `embedding = NULL`.

## What You Have

### Working Infrastructure ✅

1. **pgvector columns** ready in database:
   ```sql
   memory_logs.embedding: Vector(768) -- NULL for all 487 records
   mental_notes.embedding: Vector(768) -- NULL for 1 record
   ```

2. **EmbeddingService** exists and works:
   - Path: `src/modules/embeddings/service/embedding_service.py`
   - Methods:
     - `generate_embedding(text)` - Single text
     - `generate_embeddings_batch(texts)` - Batch processing
   - Provider: Google text-embedding-004 (768 dimensions)

3. **Event handlers** already configured:
   - `MemoryLogStorageHandler` - Listens to `memory_log.stored`
   - Auto-generates embeddings for new memory logs
   - Updates PostgreSQL + stores in ChromaDB

### What Needs to be Done

Create a **one-time batch script** to generate embeddings for the 487 migrated memory logs (and 1 mental note).

## Recommended Approach

### Option A: Simple Event Re-trigger (Recommended)

Query existing records and re-emit events to trigger the existing handlers.

**Pros:**
- Reuses existing event handlers
- Automatic ChromaDB storage
- Proven workflow

**Pseudo-code:**
```python
# scripts/generate_embeddings_for_migrated_data.py

# 1. Query records where embedding IS NULL
memory_logs = await repo.get_all_without_embeddings()

# 2. For each record, emit memory_log.stored event
for log in memory_logs:
    event_bus.publish("memory_log.stored", {
        "memory_log_id": log.id,
        "task": log.task,
        "agent": log.agent,
        "date": log.date,
        "raw_data": log.raw_data,
        "user_id": log.user_id,
        "project_id": log.project_id,
    })

# Event handler will:
# - Generate embedding via EmbeddingService
# - Update memory_logs.embedding
# - Store vector in ChromaDB
```

### Option B: Direct Batch Processing

Generate embeddings directly without events.

**Pros:**
- Simpler, more direct
- Faster (no event overhead)

**Cons:**
- Need to manually update both PostgreSQL and ChromaDB
- Duplicate logic from event handlers

**Pseudo-code:**
```python
# 1. Query records where embedding IS NULL
memory_logs = await repo.get_all_without_embeddings()

# 2. Prepare texts for batch embedding
texts = [json.dumps(log.raw_data) for log in memory_logs]
ids = [log.id for log in memory_logs]

# 3. Generate embeddings in batch
response = await embedding_service.generate_embeddings_batch(texts)

# 4. Update database
for i, log_id in enumerate(ids):
    embedding = response.embeddings[i]
    await repo.update_embedding(log_id, embedding)

# 5. Store in ChromaDB (if needed)
# ... manual storage logic
```

## Implementation Details

### Key Files to Reference

1. **Existing handler:**
   - `src/events/internal_handlers/handlers/memory_log_handler.py`
   - Shows how event handler generates embeddings

2. **Embedding service:**
   - `src/modules/embeddings/service/embedding_service.py`
   - `generate_embeddings_batch()` method

3. **Repository:**
   - `src/database/repositories/memory_log_repository.py`
   - Need to add: `get_all_without_embeddings()` method
   - Need to add: `update_embedding(id, embedding)` method

4. **Event initialization:**
   - `src/api/dependencies/event_handlers.py`
   - Shows how event handlers are initialized

### Script Structure

```python
"""
Generate embeddings for migrated memory logs and mental notes.

Usage:
    python scripts/generate_embeddings_for_migrated_data.py --dry-run
    python scripts/generate_embeddings_for_migrated_data.py
"""

import argparse
import asyncio
from src.api.bootstrap.config import load_app_config, load_service_config
from src.api.dependencies.event_handlers import initialize_event_handlers
from src.database import DatabaseManager
from src.modules.core import EventBus, Logger
from src.modules.embeddings import EmbeddingService, GoogleEmbeddingProvider

async def main(dry_run: bool):
    # 1. Initialize services (event bus, embedding, database)
    # 2. Initialize event handlers
    # 3. Query records where embedding IS NULL
    # 4. Re-emit events for each record
    # 5. Wait for handlers to complete
    # 6. Report results

if __name__ == "__main__":
    asyncio.run(main())
```

### Batch Processing Considerations

**For 487 records:**
- Batch size: 50-100 records at a time (Google API limits)
- Estimated time: ~5-10 minutes (depending on API rate limits)
- Cost: ~487 * $0.00002 = $0.01 (Google text-embedding-004 pricing)

## Mental Notes

The same approach works for mental notes:
- 1 record with `embedding = NULL`
- Same event handler pattern: `mental_note.stored`
- Handler: `src/events/internal_handlers/handlers/mental_note_handler.py` (probably exists)

## Success Criteria

After running the script:

```sql
-- Should return 0
SELECT COUNT(*) FROM memory_logs WHERE embedding IS NULL;

-- Should return 0
SELECT COUNT(*) FROM mental_notes WHERE embedding IS NULL;

-- Verify embeddings exist
SELECT id, task,
       CASE WHEN embedding IS NOT NULL THEN 'HAS EMBEDDING' ELSE 'NO EMBEDDING' END
FROM memory_logs
LIMIT 10;
```

## Next Steps for Implementation

1. **Create the script** (`scripts/generate_embeddings_for_migrated_data.py`)
2. **Add repository methods** if needed:
   - `get_all_without_embeddings()`
   - `update_embedding(id, embedding)`
3. **Test with dry-run** on 5-10 records first
4. **Run full batch** for all 487 records
5. **Verify embeddings** in database
6. **Test semantic search** to confirm vectors work

## References

- Migration scripts created this session:
  - `scripts/migrate_temp_to_postgres.py` - Memory logs migration
  - `scripts/migrate_mental_notes_to_postgres.py` - Mental notes migration

- Records migrated:
  - 487 memory logs with `embedding = NULL`
  - 1 mental note with `embedding = NULL`
  - All have `user_id = 84e17260-ff03-409b-bf30-0b5ba52a2ab4`
  - All have `project_id = 84e17260-ff03-409b-bf30-0b5ba52a2ab4`

## Estimated Effort

- Script creation: 30 minutes
- Testing: 15 minutes
- Full batch run: 5-10 minutes
- **Total: ~1 hour**

---

*This is a one-time operation. After embeddings are generated, all future memory logs will automatically get embeddings via the event handler system.*

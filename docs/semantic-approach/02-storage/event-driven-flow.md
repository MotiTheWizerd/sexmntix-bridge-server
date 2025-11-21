# Event-Driven Storage Flow

## Overview

Storage is non-blocking: PostgreSQL writes complete immediately, ChromaDB updates happen asynchronously via events.

## Complete Flow

```
API Request: POST /memory-logs
       ↓
[SYNCHRONOUS - User Waits]
       ↓
1. Create in PostgreSQL
       • INSERT INTO memory_logs
       • Returns memory_log_id
       • ~5-10ms
       ↓
2. Return Success to User
       • User sees: 201 Created
       • Total latency: ~10-20ms
       ↓
3. Emit Event: "memory_log.stored"
       • Payload: {memory_log_id, raw_data, user_id, project_id}
       • Non-blocking event bus
       ↓
[ASYNCHRONOUS - Background]
       ↓
4. MemoryLogStorageHandler Receives Event
       ↓
5. Extract Searchable Text
       • MemoryTextExtractor.extract()
       • Combines: task, summary, solution, tags, etc.
       • ~1-5ms
       ↓
6. Generate Embedding
       • EmbeddingService.generate_embedding(text)
       • Cache check → API call if needed
       • ~200-500ms (or <1ms if cached)
       ↓
7. Store in ChromaDB
       • VectorRepository.add_memory()
       • collection.add(id, embedding, document, metadata)
       • ~10-20ms
       ↓
8. Update PostgreSQL with Embedding
       • UPDATE memory_logs SET embedding = ...
       • ~5-10ms
       ↓
9. Emit Event: "vector.stored"
       • Confirmation event
       • Can trigger further processing
       ↓
Complete (~500ms total background time)
```

## Why Event-Driven?

### User Experience
**Without events (synchronous)**:
```
Request → PostgreSQL → Embed → ChromaDB → Response
Total: 5ms + 300ms + 20ms = 325ms

User waits 325ms for every memory creation
```

**With events (asynchronous)**:
```
Request → PostgreSQL → Response (user done)
Background: Embed → ChromaDB

User waits: 10ms
Background: 320ms (doesn't block user)
```

**Result**: 30x faster user experience

## Best Practices

1. **Idempotent handlers**: Event may be delivered multiple times
2. **Dead letter queue**: For events that repeatedly fail
3. **Monitoring**: Track event processing latency
4. **Backpressure**: Slow down API if queue too deep
5. **Graceful degradation**: PostgreSQL still works if event processing fails

---

*Part of the [Storage Documentation](./README.md)*

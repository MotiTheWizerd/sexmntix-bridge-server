# Dual Storage Architecture

## Why Two Databases?

### The Problem
- **Vector search** requires specialized indexing (HNSW)
- **Relational data** needs SQL, transactions, joins
- No single database excels at both

### The Solution
Use **PostgreSQL** and **ChromaDB** together, each doing what it does best.

## Responsibility Division

| Responsibility | PostgreSQL | ChromaDB |
|----------------|------------|----------|
| **Primary storage** | ✅ | ❌ |
| **Relational queries** | ✅ | ❌ |
| **Transactions** | ✅ | ❌ |
| **Vector similarity search** | ❌ | ✅ |
| **HNSW indexing** | ❌ | ✅ |
| **Fast nearest neighbor** | ❌ | ✅ |
| **Metadata filtering** | ✅ | ✅ |
| **Backup/restore** | ✅ | ⚠️ |

## Data Flow

```
Write Path:
PostgreSQL → (event) → ChromaDB
    ↓                      ↓
Source of truth      Search index

Read Path (Search):
Query → ChromaDB → Results
```

## What's Stored Where

### PostgreSQL (`memory_logs` table)
```sql
- id (primary key)
- user_id
- project_id
- raw_data (JSONB) -- Full memory content
- embedding (vector(768)) -- Backup of embedding
- created_at
- updated_at
```

### ChromaDB (collection per tenant)
```python
- id: "memory_log_123"
- embedding: [768 floats] -- For similarity search
- document: JSON string -- Full memory content
- metadata: {date, task, component, ...} -- For filtering
```

## Why This Works

1. **PostgreSQL** = Single source of truth
   - All data persisted here first
   - Easy backup/restore
   - Supports complex queries

2. **ChromaDB** = Search optimization
   - Fast vector similarity
   - Rebuilt from PostgreSQL if needed
   - Optimized for embeddings

3. **Event-driven sync** = Loose coupling
   - PostgreSQL write doesn't wait for ChromaDB
   - Failures handled gracefully
   - Can replay events if needed

## Consistency Model

**Eventually consistent**: ChromaDB may lag PostgreSQL by milliseconds.

```
T0: Write to PostgreSQL (user sees success)
T0+10ms: Event emitted
T0+500ms: ChromaDB updated
```

**Why acceptable?**
- Search doesn't need immediate consistency
- Users don't search for just-created memories instantly
- Event processing is usually <1 second

## Failure Scenarios

### PostgreSQL Down
```
Effect: Cannot create new memories
Action: Return error to user (expected)
```

### ChromaDB Down
```
Effect: Cannot search, but writes still work
Action: Queue events for replay when ChromaDB recovers
```

### Event Processing Failure
```
Effect: Memory in PostgreSQL but not ChromaDB
Action: Retry event processing, dead letter queue
```

## Migration & Rebuild

If ChromaDB data is lost or corrupt:

```python
async def rebuild_chromadb_from_postgres():
    """Rebuild ChromaDB from PostgreSQL"""
    memories = db.query(MemoryLog).all()

    for memory in memories:
        # Re-extract and re-embed if needed
        text = extract_searchable_text(memory)
        embedding = embedding_service.generate_embedding(text)

        # Store in ChromaDB
        vector_repo.add_memory(
            id=f"memory_log_{memory.id}",
            embedding=embedding,
            document=memory.raw_data,
            metadata=extract_metadata(memory)
        )
```

**Recovery time**: ~1-2 hours for 100K memories

---

*Part of the [Storage Documentation](./README.md)*

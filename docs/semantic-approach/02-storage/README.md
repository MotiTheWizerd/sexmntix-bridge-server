# Vector Storage Module

## Overview

The storage module manages the dual-database architecture (PostgreSQL + ChromaDB) for storing and retrieving memory embeddings with multi-tenant isolation.

## What You'll Learn

- [Dual Storage Strategy](./dual-storage.md) - Why PostgreSQL + ChromaDB
- [ChromaDB Details](./chromadb.md) - Vector database setup and collections
- [PostgreSQL Details](./postgresql.md) - Schema and pgvector integration
- [Multi-Tenancy](./multi-tenancy.md) - User/project isolation strategy
- [Event-Driven Flow](./event-driven-flow.md) - Non-blocking storage via events
- [Text Extraction](./text-extraction.md) - Converting memories to searchable text

## Quick Facts

| Aspect | Details |
|--------|---------|
| **Primary DB** | PostgreSQL (persistent, relational) |
| **Vector DB** | ChromaDB (fast similarity search) |
| **Isolation** | Collection-based (hash of user:project) |
| **Storage Model** | Event-driven (async, non-blocking) |
| **Vector Index** | HNSW (Hierarchical Navigable Small World) |

## Storage Architecture

```
Memory Log Created
       ↓
   PostgreSQL (sync)
       ↓
   Emit Event (async)
       ↓
┌──────────────────┐
│ Background       │
│ Handler          │
│                  │
│ 1. Extract text  │
│ 2. Generate      │
│    embedding     │
│ 3. Store in      │
│    ChromaDB      │
│ 4. Update        │
│    PostgreSQL    │
└──────────────────┘
```

## Why Dual Storage?

### PostgreSQL Strengths
- Persistent data storage
- Relational queries
- Transactions and ACID
- Backup and recovery

### ChromaDB Strengths
- Fast vector similarity search
- HNSW indexing
- Optimized for embeddings
- Low latency queries

**Strategy**: Use both, leverage strengths of each.

## Key Files

```
src/modules/vector_storage/
├── storage/
│   └── memory_storage_handler.py      # Main orchestrator
│
├── text_extraction/
│   └── memory_text_extractor.py       # Extract searchable text
│
└── search/
    └── handler/
        └── base_handler.py             # Search public API

src/infrastructure/chromadb/
├── client.py                           # ChromaDB client
├── collection.py                       # Collection management
├── repository.py                       # Vector operations
└── operations/
    ├── search_operations.py           # Search operations
    └── memory/
        └── memory_logger.py           # Memory CRUD

src/database/models/
└── memory_log.py                      # PostgreSQL model
```

## Common Operations

### Store Memory

```python
# 1. Create in PostgreSQL (sync)
memory_log = db.create_memory_log(
    user_id="user123",
    project_id="project456",
    raw_data={...}
)

# 2. Event automatically triggers background storage
# → Extract searchable text
# → Generate embedding
# → Store in ChromaDB
# → Update PostgreSQL with embedding
```

### Search Memories

```python
# Query is automatically embedded and searched
results = search_handler.search_similar_memories(
    query="authentication bug fix",
    user_id="user123",
    project_id="project456",
    limit=10
)
```

## Multi-Tenancy

Each user/project gets isolated storage:

```
User: "user123"
Project: "project456"
       ↓
Hash: SHA256("user123:project456")[:16]
     = "a1b2c3d4e5f6g7h8"
       ↓
Collection: "memory_logs_a1b2c3d4e5f6g7h8"
```

**Result**: Complete data isolation, no leakage between tenants.

## Performance

| Operation | Latency | Notes |
|-----------|---------|-------|
| **Store (PostgreSQL)** | ~5-10ms | Synchronous, user waits |
| **Store (ChromaDB)** | ~10-20ms | Asynchronous, background |
| **Search** | ~100-300ms | Includes embedding generation |
| **Bulk import** | Variable | Use batch processing |

## Next Steps

- **Understand strategy**: [Dual Storage](./dual-storage.md)
- **ChromaDB setup**: [ChromaDB Details](./chromadb.md)
- **Isolation model**: [Multi-Tenancy](./multi-tenancy.md)
- **Event flow**: [Event-Driven Flow](./event-driven-flow.md)

---

*Part of the [Semantic Approach Documentation](../README.md)*

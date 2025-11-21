# ChromaDB Vector Database

## Overview

ChromaDB provides fast vector similarity search using HNSW indexing for semantic memory retrieval.

## Setup

### Single Shared Instance
```python
# Located at: ./data/chromadb
client = chromadb.PersistentClient(path="./data/chromadb")
```

**Why single instance?**
- Efficient resource usage
- Shared connection pool
- Centralized management
- Multi-tenancy via collections

## Collection Strategy

### Naming Convention
```
Format: {prefix}_{hash16}

prefix: "memory_logs" or "mental_notes"
hash16: SHA256(user_id:project_id)[:16]

Example: memory_logs_a1b2c3d4e5f6g7h8
```

### Collection per Tenant
```
User A, Project 1 → memory_logs_abc123...
User A, Project 2 → memory_logs_def456...
User B, Project 1 → memory_logs_ghi789...
```

**Benefits**:
- Complete data isolation
- Independent scaling
- Easy deletion (drop collection)
- Filtered queries (no need to filter by user_id)

## Data Model

### What's Stored

```python
collection.add(
    ids=["memory_log_123"],
    embeddings=[[0.1, 0.2, ..., 0.8]],  # 768 floats
    documents=['{"task": "Fix bug", ...}'],  # JSON string
    metadatas=[{
        "date": "2025-01-15",
        "task": "Fix auth bug",
        "component": "auth-service",
        "tags": "bug,security"
    }]
)
```

### Field Purposes

| Field | Purpose | Searchable |
|-------|---------|------------|
| **ids** | Unique identifier | ✅ (exact match) |
| **embeddings** | Vector for similarity | ✅ (similarity) |
| **documents** | Full content | ❌ (returned only) |
| **metadatas** | Structured filters | ✅ (where clauses) |

## HNSW Indexing

### What is HNSW?

**Hierarchical Navigable Small World** graph index
- Fast approximate nearest neighbor search
- O(log n) query time
- High recall (>95% of true neighbors found)

### How It Works

```
Level 2:  •──────•
           ╲    ╱
Level 1:    •──•──•──•
             ╲│╱│╲│╱
Level 0:      •─•─•─•─•─•─•

Query enters at top, navigates down to nearest neighbor
```

**Trade-off**:
- Build time: Slower (more connections)
- Query time: Fast (fewer hops)
- Memory: Higher (store graph)

## Distance Metric

### L2 (Euclidean) Distance

```python
distance = sqrt(sum((a[i] - b[i])^2 for i in range(768)))
```

**Properties**:
- 0 = identical vectors
- Higher = more different
- Range: [0, ∞)

### Conversion to Similarity

```python
# ChromaDB returns distances
# Convert to similarity score (0-1)
similarity = 1 - (distance / 2)

# Assumes normalized vectors, max distance ≈ 2
```

## Common Operations

### Create Collection

```python
collection = client.get_or_create_collection(
    name="memory_logs_a1b2c3d4e5f6g7h8",
    metadata={"hnsw:space": "l2"}
)
```

### Add Memory

```python
collection.add(
    ids=[f"memory_log_{memory_id}"],
    embeddings=[embedding],
    documents=[json.dumps(memory.raw_data)],
    metadatas=[{
        "date": memory.created_at.isoformat(),
        "task": memory.task,
        ...
    }]
)
```

### Search

```python
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=10,
    where={"component": "auth-service"},  # Optional filter
    include=["documents", "metadatas", "distances"]
)
```

### Delete Memory

```python
collection.delete(ids=[f"memory_log_{memory_id}"])
```

### Drop Collection

```python
client.delete_collection(name="memory_logs_...")
```

## Performance

| Operation | Latency | Notes |
|-----------|---------|-------|
| **Add** | ~10-20ms | Per memory |
| **Query** | ~10-50ms | For 10 results |
| **Batch add** | ~100ms | 100 memories |
| **Delete** | ~5ms | Per memory |

## Metadata Filtering

### Filter Syntax

```python
# Equal
where={"component": "auth-service"}

# Not equal
where={"component": {"$ne": "auth-service"}}

# Greater than
where={"date": {"$gte": "2025-01-01"}}

# In list
where={"component": {"$in": ["auth", "user"]}}

# AND
where={
    "$and": [
        {"component": "auth"},
        {"date": {"$gte": "2025-01-01"}}
    ]
}
```

## Limitations

1. **No transactions**: Each operation is independent
2. **No joins**: Can't join across collections
3. **Limited aggregation**: No GROUP BY or complex queries
4. **Metadata size**: Keep metadata small (<1KB per entry)

---

*Part of the [Storage Documentation](./README.md)*

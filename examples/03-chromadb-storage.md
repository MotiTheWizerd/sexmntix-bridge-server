# ChromaDB Vector Storage

## What is ChromaDB?

ChromaDB is an **open-source vector database** optimized for:
- Storing vector embeddings
- Fast similarity search
- Persistent local storage
- No external server required

---

## Configuration

### File Location
`semantix-brain/src/infrastructure/chromadb/client.py`

### Storage Path
```
semantix-brain/data/chromadb/
```

### Client Setup
```python
import chromadb
from chromadb.config import Settings

client = chromadb.PersistentClient(
    path="./data/chromadb",
    settings=Settings(
        anonymized_telemetry=False
    )
)
```

---

## Collection Structure

### What is a Collection?
Think of it as a "table" in a traditional database, but for vectors.

### Default Collection
```python
collection_name = "sementix_memories"
```

### Multi-Project Support
```python
# Per-project isolation
collection_name = f"sementix_memories_{project_id}"
```

Each project gets its own vector search space.

---

## Data Storage Format

When you add a memory to ChromaDB, it stores **4 components**:

### 1. ID (Unique Identifier)
```python
id = memory.file_name or f"{memory.task}_{memory.date}"
# Example: "permission-dialog-redesign_2025-11-12"
```

### 2. Embedding (Vector)
```python
embedding = [0.0234, -0.1234, 0.5678, ...]  # ~768 dimensions
```

### 3. Document (Full JSON)
```python
document = {
    "task": "permission-dialog-redesign",
    "component": "ui-permission-system",
    "date": "2025-11-12",
    "summary": "Complete redesign...",
    "root_cause": "...",
    "solution": "...",
    "tags": ["permission-dialog", "ui-redesign"],
    # ... all other fields
}
```

### 4. Metadata (Flat Dict for Filtering)
```python
metadata = {
    "task": "permission-dialog-redesign",
    "agent": "claude",
    "component": "ui-permission-system",
    "date": "2025-11-12",
    "tags": "permission-dialog,ui-redesign,glassmorphism",
    "time_period": "recent",
    "quarter": "Q4 2025",
    "year": "2025"
}
```

---

## HNSW Index

### What is HNSW?
**Hierarchical Navigable Small World** - an algorithm for fast approximate nearest neighbor search.

### How It Works
- Builds a graph structure of vectors
- Enables sub-linear time search
- Trade-off: Speed vs. Perfect accuracy

### Index Rebuild Trigger
```python
# After adding memory
collection.add(ids, embeddings, documents, metadatas)

# Force immediate index update
collection.count()  # Triggers HNSW rebuild
```

### Why Force Rebuild?
- ChromaDB lazy-loads index by default
- New memories wouldn't be searchable immediately
- Calling `.count()` forces index refresh
- Makes memories searchable without server restart

**Reference:** See memory `chromadb-hnsw-index-immediate-persistence-fix`

---

## Storage Operations

### Add Memory
**File:** `semantix-brain/src/modules/memory/repository.py`

```python
async def add(memory: Memory, embedding: list[float]) -> Memory:
    # Prepare data
    memory_id = self._generate_id(memory)
    metadata = self._prepare_metadata(memory)
    document = memory.model_dump_json()

    # Store in ChromaDB
    collection = await self._get_collection()
    collection.add(
        ids=[memory_id],
        embeddings=[embedding],
        documents=[document],
        metadatas=[metadata]
    )

    # Force index rebuild
    collection.count()

    return memory
```

### Get by ID
```python
async def get_by_id(memory_id: str) -> Memory | None:
    collection = await self._get_collection()
    result = collection.get(ids=[memory_id])

    if result["documents"]:
        return Memory.model_validate_json(result["documents"][0])
    return None
```

### Search (Vector Similarity)
```python
async def search(
    query_embedding: list[float],
    limit: int = 10,
    where_filter: dict | None = None
) -> list[SearchResult]:
    collection = await self._get_collection()

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=limit,
        where=where_filter,
        include=["documents", "metadatas", "distances"]
    )

    # Convert to SearchResult objects
    # Apply recency boosting
    # Return ranked results
```

---

## Metadata Filtering

### Basic Filtering
```python
# Find memories by component
where = {"component": "ui-permission-system"}

# Find memories by agent
where = {"agent": "claude"}
```

### Date Range Filtering
```python
# Last 7 days
where = {
    "date": {
        "$gte": "2025-11-05"
    }
}

# Date range
where = {
    "date": {
        "$gte": "2025-10-01",
        "$lte": "2025-10-31"
    }
}
```

### Combined Filters
```python
where = {
    "$and": [
        {"component": "ui-permission-system"},
        {"date": {"$gte": "2025-11-01"}}
    ]
}
```

---

## Distance Metrics

### L2 Distance
ChromaDB uses **L2 (Euclidean) distance** by default:
```
distance = sqrt(sum((a[i] - b[i])^2))
```

### Converting to Similarity Score
**File:** `semantix-brain/src/modules/memory/repository.py`

```python
def _calculate_similarity(distance: float) -> float:
    """
    Convert L2 distance to similarity percentage.

    L2 distance range: 0 to ~2.0
    - 0 = identical vectors
    - 2 = completely different

    Similarity: 0% to 100%
    """
    return max(0.0, 1.0 - (distance / 2.0))
```

### Example Conversions
```
L2 Distance    Similarity
0.0         →  100%
0.5         →  75%
1.0         →  50%
1.5         →  25%
2.0         →  0%
```

---

## Persistence

### Automatic Persistence
- ChromaDB auto-saves to disk
- No manual save operations needed
- Survives server restarts

### Data Location
```
semantix-brain/data/chromadb/
├── chroma.sqlite3          # Metadata database
└── <collection_uuid>/      # Vector data
    ├── index/              # HNSW index files
    └── data/               # Raw vectors
```

### Backup Strategy
Simply copy the entire `data/chromadb/` directory:
```bash
cp -r data/chromadb data/chromadb.backup
```

---

## Multi-Project Isolation

### Why?
Different projects need separate memory spaces:
- VS Code extension: `sementix_memories_vscode-ext`
- CLI tool: `sementix_memories_cli`
- Default: `sementix_memories`

### Implementation
```python
async def _get_collection(self, project_id: str | None = None):
    collection_name = "sementix_memories"

    if project_id:
        collection_name = f"{collection_name}_{project_id}"

    # Cache collections for performance
    if collection_name not in self._collections:
        self._collections[collection_name] = self.client.get_or_create_collection(
            name=collection_name
        )

    return self._collections[collection_name]
```

---

## Performance Characteristics

### Add Operation
- **Time:** ~50-200ms (depends on Google API)
- **Bottleneck:** Embedding generation, not ChromaDB

### Search Operation
- **Time:** ~10-50ms for 1000s of vectors
- **Scalability:** Sub-linear with HNSW index
- **Accuracy:** ~95% (approximate nearest neighbors)

### Storage Size
- **Vector:** ~3KB per embedding (768 floats)
- **Document:** Variable (JSON size)
- **Metadata:** ~1KB per memory
- **Total:** ~5-10KB per memory

### Example
1000 memories ≈ 5-10 MB

---

## Key Files Reference

| File | Responsibility |
|------|----------------|
| `src/infrastructure/chromadb/client.py` | ChromaDB client wrapper |
| `src/modules/memory/repository.py` | CRUD operations, search |
| `src/infrastructure/config/settings.py` | Storage path configuration |

---

## Python Implementation for Your Use

If you want to replicate this in another Python project:

```python
import chromadb

# 1. Create persistent client
client = chromadb.PersistentClient(path="./data/chromadb")

# 2. Get or create collection
collection = client.get_or_create_collection("my_memories")

# 3. Add vectors
collection.add(
    ids=["memory_1"],
    embeddings=[[0.1, 0.2, 0.3, ...]],  # Your vector
    documents=['{"task": "example"}'],   # JSON string
    metadatas=[{"task": "example"}]      # Flat dict
)

# 4. Search
results = collection.query(
    query_embeddings=[[0.1, 0.2, 0.3, ...]],
    n_results=5
)

# 5. Force index rebuild
collection.count()
```

That's all you need! ChromaDB handles the rest.

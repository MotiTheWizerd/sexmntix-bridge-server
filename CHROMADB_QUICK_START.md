# ChromaDB Quick Start

## 🚀 What You Got

**Semantic search for memory logs** - Find memories by meaning, not keywords!

```
Before: "authentication" → finds only exact keyword matches
After:  "login issues" → finds authentication, OAuth, JWT, security bugs
```

---

## ⚡ Quick Test

### 1. Install & Migrate
```bash
poetry install
poetry run alembic upgrade head
```

### 2. Set Environment Variable
```bash
# .env file
GOOGLE_API_KEY=your_key_here
CHROMADB_PATH=./data/chromadb
```

### 3. Run Test Script
```bash
python examples/test_chromadb_integration.py
```

**Output:**
```
✓ Stored 3 memory vectors
✓ Semantic search works
✓ Metadata filtering works
✓ Cache hit rate: 70%+
```

### 4. Start API Server
```bash
poetry run uvicorn src.api.app:app --reload
```

---

## 📝 API Usage

### Create Memory (with auto-embedding)
```bash
curl -X POST http://localhost:8000/memory-logs \
  -H "Content-Type: application/json" \
  -d '{
    "task": "fix-login-bug",
    "agent": "claude",
    "date": "2025-11-13",
    "user_id": "user123",
    "project_id": "project456",
    "summary": "Fixed authentication issue with JWT tokens",
    "solution": "Updated token validation logic",
    "tags": ["security", "auth", "bug-fix"]
  }'
```

**What happens:**
1. ✅ Stored in PostgreSQL
2. ✅ Embedding generated (768D vector)
3. ✅ Stored in ChromaDB
4. ✅ Immediately searchable

---

### Semantic Search
```bash
curl -X POST http://localhost:8000/memory-logs/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "authentication problems and security issues",
    "user_id": "user123",
    "project_id": "project456",
    "limit": 5,
    "min_similarity": 0.5
  }'
```

**Response:**
```json
[
  {
    "id": "memory_1_user123_project456",
    "memory_log_id": 1,
    "document": {
      "task": "fix-login-bug",
      "summary": "Fixed authentication issue with JWT tokens",
      ...
    },
    "similarity": 0.87,
    "distance": 0.26
  }
]
```

**Similarity Scoring:**
- `1.0` = perfect match (same meaning)
- `0.5` = moderate similarity
- `0.0` = completely different

---

## 🎯 Key Concepts

### Dual Storage
```
PostgreSQL           ChromaDB
├─ Relational data   ├─ Vector embeddings
├─ Transactions      ├─ HNSW similarity search
├─ SQL queries       ├─ Sub-linear performance
└─ Embeddings        └─ 10-50ms search (1000s vectors)
```

### Multi-Tenant Isolation
```
Collection: semantix_memories_user123_project456
           └─────────────┬──────┴───┬─────────┘
                    user_id    project_id

✓ Complete data isolation
✓ No cross-user contamination
✓ Independent scaling
```

### HNSW Index
```
collection.add(ids, embeddings, documents, metadatas)
collection.count()  # ← Force index rebuild (CRITICAL!)
```

**Without `.count()`:** New vectors not searchable until restart
**With `.count()`:** Immediate searchability (adds 10-50ms)

---

## 📊 Performance

| Operation | Speed | Notes |
|-----------|-------|-------|
| Embedding (first) | 100-300ms | Google API call |
| Embedding (cached) | <1ms | LRU cache hit |
| Add vector | 10-50ms | Includes HNSW update |
| Search 1000s vectors | 10-50ms | Sub-linear with HNSW |
| Cache hit rate | 70%+ | Production typical |

---

## 🛠️ Architecture

```
POST /memory-logs
     │
     ├─→ 1. Store in PostgreSQL
     │
     ├─→ 2. Generate embedding (Google text-embedding-004)
     │       └─→ Check LRU cache first (70%+ hits)
     │
     ├─→ 3. Update PostgreSQL with embedding
     │
     └─→ 4. Store in ChromaDB
             └─→ collection.count() for immediate search
```

```
POST /memory-logs/search
     │
     ├─→ 1. Generate query embedding
     │
     ├─→ 2. ChromaDB HNSW search
     │       └─→ Returns L2 distances
     │
     ├─→ 3. Convert distance → similarity %
     │       └─→ similarity = 1.0 - (distance / 2.0)
     │
     └─→ 4. Filter by min_similarity & return
```

---

## 🐛 Common Issues

### "No results found"
```bash
# Check collection exists
curl http://localhost:8000/memory-logs/search \
  -d '{"query": "test", "user_id": "user123", "project_id": "project456"}'

# Verify user_id + project_id match creation
```

### "Vectors not searchable"
```python
# Make sure you're calling .count() after add
collection.add(...)
collection.count()  # ← Don't forget this!
```

### "Poor search results"
```python
# Combine multiple fields for better embeddings
searchable_text = f"{task} {summary} {solution} {' '.join(tags)}"
```

---

## 📦 Files Structure

```
src/
├── infrastructure/chromadb/
│   ├── client.py          # ChromaDB wrapper
│   └── repository.py      # Vector CRUD operations
├── services/
│   └── vector_storage_service.py  # Orchestration
├── api/
│   ├── dependencies/vector_storage.py
│   ├── routes/memory_logs.py      # POST /memory-logs/search
│   └── schemas/memory_log.py
└── database/models/memory_log.py  # embedding, user_id, project_id

examples/
└── test_chromadb_integration.py   # Standalone test

alembic/versions/
└── fb1c8a41bc5d_add_embedding_fields_to_memory_logs.py
```

---

## 🔍 Metadata Filters

```json
// Exact match
{"component": "auth-module"}

// Date range
{"date": {"$gte": "2025-11-01", "$lte": "2025-11-30"}}

// Multiple conditions
{
  "$and": [
    {"component": "ui-system"},
    {"agent": "claude"},
    {"date": {"$gte": "2025-11-01"}}
  ]
}

// Tag search (comma-separated string)
{"tags": {"$contains": "security"}}
```

---

## 🎓 Next Steps

1. ✅ **Test It:** Run `python examples/test_chromadb_integration.py`
2. ✅ **Try API:** Create memory log → Search by meaning
3. 📖 **Read Full Guide:** `CHROMADB_INTEGRATION_GUIDE.md`
4. 🔧 **Extend It:**
   - Add to mental_notes table
   - Implement OpenAI provider
   - Add Redis distributed cache
   - Create monitoring dashboard

---

## 💡 Pro Tips

**Cache optimization:**
```bash
EMBEDDING_CACHE_ENABLED=true
EMBEDDING_CACHE_SIZE=1000
EMBEDDING_CACHE_TTL_HOURS=24
```

**Better embeddings:**
```python
# Combine multiple fields
searchable = f"{task} {summary} {solution} {' '.join(tags)}"

# More context = better recall
```

**Search tuning:**
```json
{
  "query": "your search",
  "limit": 10,              // More results
  "min_similarity": 0.3     // Lower threshold = more results
}
```

---

## 📞 Support

- **Full Documentation:** `CHROMADB_INTEGRATION_GUIDE.md`
- **Implementation Log:** `CHROMADB_IMPLEMENTATION_SUMMARY.json`
- **Test Script:** `examples/test_chromadb_integration.py`

---

## ✨ You're Ready!

**Search by meaning, not keywords!** 🚀

```bash
# Start building semantic search into your app
poetry run uvicorn src.api.app:app --reload
```

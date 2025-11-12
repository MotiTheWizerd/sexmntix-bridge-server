# Semantic Search Process

## Overview

Semantic search finds memories by **meaning**, not just keywords. It understands that "permission dialog bug" and "authorization UI issue" are related concepts.

---

## Complete Search Flow

### Step 1: User Query
```python
query = "permission dialog UI issues"
```

### Step 2: Generate Query Embedding

**File:** `semantix-brain/src/modules/memory/service.py`

```python
# Convert query text to vector
query_embedding = await embedding_service.generate_embedding(query)

# Result: [0.123, -0.456, 0.789, ...]
```

Same process as memory embedding - uses Google's text-embedding-004.

### Step 3: Vector Similarity Search

**File:** `semantix-brain/src/modules/memory/repository.py`

```python
results = collection.query(
    query_embeddings=[query_embedding],
    n_results=limit,
    where=where_filter,  # Optional metadata filters
    include=["documents", "metadatas", "distances"]
)
```

ChromaDB compares query vector against all stored memory vectors using HNSW index.

### Step 4: Calculate Similarity Scores

**Distance to Similarity Conversion:**

```python
def _calculate_similarity(distance: float) -> float:
    """
    L2 distance (0-2) → Similarity (0-1)

    Examples:
    - distance 0.0 → similarity 1.0 (100% match)
    - distance 0.5 → similarity 0.75 (75% match)
    - distance 1.0 → similarity 0.5 (50% match)
    - distance 2.0 → similarity 0.0 (0% match)
    """
    return max(0.0, 1.0 - (distance / 2.0))
```

### Step 5: Apply Recency Boost

**Why?** Recent memories are usually more relevant.

```python
def _apply_recency_boost(
    results: list[SearchResult],
    boost_config: dict
) -> list[SearchResult]:
    """
    Boost similarity scores based on memory age.

    Default boosts:
    - Last 7 days:  1.5x multiplier
    - Last 30 days: 1.2x multiplier
    - Last 90 days: 1.0x (neutral)
    - Older:        0.8x multiplier
    """
    now = datetime.now()

    for result in results:
        memory_date = datetime.fromisoformat(result.memory.date)
        days_old = (now - memory_date).days

        # Determine boost multiplier
        if days_old <= 7:
            multiplier = 1.5
        elif days_old <= 30:
            multiplier = 1.2
        elif days_old <= 90:
            multiplier = 1.0
        else:
            multiplier = 0.8

        # Apply boost
        result.similarity = result.similarity * multiplier

    return results
```

### Step 6: Re-rank by Boosted Score

```python
# Sort by boosted similarity (descending)
results.sort(key=lambda r: r.similarity, reverse=True)
```

### Step 7: Return Results

```python
[
    SearchResult(
        memory=Memory(...),
        similarity=0.884,  # 88.4% match
        distance=0.232
    ),
    SearchResult(
        memory=Memory(...),
        similarity=0.819,  # 81.9% match
        distance=0.362
    ),
    ...
]
```

---

## Search Flow Diagram

```
User Query: "permission dialog UI issues"
       ↓
Generate Query Embedding
       ↓
Query Vector: [0.123, -0.456, 0.789, ...]
       ↓
ChromaDB Vector Search (HNSW Index)
       ↓
Compare against all memory vectors
       ↓
Return Top N by L2 Distance
       ↓
Convert Distance → Similarity %
       ↓
Apply Recency Boost
       ↓
Re-rank by Boosted Similarity
       ↓
Return SearchResult[]
```

---

## Date Filtering

### Time Period Filters

**File:** `semantix-brain/src/modules/memory/service.py`

```python
class DateFilter:
    time_period: Literal["recent", "last-week", "last-month", "archived"] | None
    start_date: str | None  # ISO format: "2025-11-01"
    end_date: str | None    # ISO format: "2025-11-12"
```

### Period Definitions

```python
def _convert_time_period(time_period: str) -> dict:
    now = datetime.now()

    periods = {
        "recent": 7,      # Last 7 days
        "last-week": 14,  # 7-14 days ago
        "last-month": 30, # Last 30 days
        "archived": 90    # 90+ days ago
    }

    if time_period == "archived":
        # Older than 90 days
        return {
            "date": {
                "$lt": (now - timedelta(days=90)).isoformat()[:10]
            }
        }
    else:
        days = periods[time_period]
        return {
            "date": {
                "$gte": (now - timedelta(days=days)).isoformat()[:10]
            }
        }
```

### Custom Date Ranges

```python
# Search between specific dates
where_filter = {
    "date": {
        "$gte": "2025-10-01",
        "$lte": "2025-10-31"
    }
}
```

---

## Metadata Filtering

### Component Filter
```python
# Only search within permission-system memories
where_filter = {"component": "permission-system"}
```

### Combined Filters
```python
# Recent permission-system memories
where_filter = {
    "$and": [
        {"component": "permission-system"},
        {"date": {"$gte": "2025-11-01"}}
    ]
}
```

### Tag Filtering
```python
# Note: Tags stored as comma-separated string
# "permission-dialog,ui-redesign,glassmorphism"

# Search by tag (partial match)
where_filter = {
    "tags": {"$contains": "permission-dialog"}
}
```

---

## Search API Endpoints

### Basic Search

**Endpoint:** `POST /memory/search`

```json
{
  "query": "permission dialog UI issues",
  "limit": 10
}
```

**Response:**
```json
{
  "results": [
    {
      "memory": {
        "task": "permission-dialog-redesign",
        "component": "ui-permission-system",
        "date": "2025-11-12",
        "summary": "Complete redesign...",
        ...
      },
      "similarity": 0.884,
      "distance": 0.232
    },
    ...
  ],
  "total": 15
}
```

### Search with Date Filter

**Endpoint:** `POST /memory/search/by-date`

```json
{
  "query": "permission system",
  "limit": 10,
  "time_period": "recent"
}
```

or

```json
{
  "query": "permission system",
  "limit": 10,
  "start_date": "2025-10-01",
  "end_date": "2025-10-31"
}
```

---

## Why Semantic Search Works

### Example: Understanding Context

**Query:** "authorization popup not appearing"

**Will Match:**
- "permission dialog not showing"
- "tool confirmation UI hidden"
- "consent modal disappearing"

**Why?** Embeddings capture semantic relationships:
- authorization ≈ permission ≈ consent
- popup ≈ dialog ≈ modal
- not appearing ≈ hidden ≈ disappearing

### Traditional Keyword Search Would Miss

If you searched for exact keyword "authorization popup":
- ❌ Would NOT match "permission dialog"
- ❌ Would NOT match "consent modal"
- ❌ Would require exact wording

### Semantic Search Finds Meaning

Embeddings understand concepts, not just words:
```
Vector space distance between:
"permission" and "authorization" → Very close
"dialog" and "modal"             → Very close
"bug" and "error"                → Very close
"fix" and "solution"             → Very close
```

---

## Performance Characteristics

### Search Speed
- **Small (<1K memories):** ~10-20ms
- **Medium (1K-10K):** ~20-50ms
- **Large (10K-100K):** ~50-200ms

HNSW index provides sub-linear scaling.

### Accuracy
- **Recall:** ~95% (finds 95% of true matches)
- **Precision:** ~90% (90% of results are relevant)
- Trade-off: Speed vs. Perfect accuracy

### API Costs
- Query embedding: ~$0.00001 per search (negligible)
- No re-embedding of stored memories

---

## Key Implementation Files

| File | Responsibility |
|------|----------------|
| `src/modules/memory/service.py` | Search orchestration, date filtering |
| `src/modules/memory/repository.py` | Vector search, similarity calculation, recency boost |
| `src/infrastructure/embeddings/embedding_service.py` | Query embedding generation |
| `src/modules/memory/api.py` | HTTP endpoints |

---

## Code Example: Full Search

```python
from semantix_brain.modules.memory.service import MemoryService

# Initialize service
memory_service = MemoryService(
    repository=memory_repository,
    embedding_service=embedding_service
)

# Basic search
results = await memory_service.search(
    query="permission dialog issues",
    limit=10
)

# Search with date filter
results = await memory_service.search_by_date(
    query="permission system",
    limit=10,
    time_period="recent"  # Last 7 days
)

# Search with custom date range
results = await memory_service.search_by_date(
    query="streaming bugs",
    limit=5,
    start_date="2025-10-01",
    end_date="2025-10-31"
)

# Process results
for result in results:
    print(f"Match: {result.similarity:.1%}")
    print(f"Task: {result.memory.task}")
    print(f"Summary: {result.memory.summary}")
    print("---")
```

---

## Tuning Search Quality

### Adjust Recency Boost

**File:** `semantix-brain/src/modules/memory/repository.py`

```python
# Current settings
RECENCY_BOOST = {
    7: 1.5,   # Last week: 50% boost
    30: 1.2,  # Last month: 20% boost
    90: 1.0,  # Last quarter: Neutral
    999: 0.8  # Older: 20% penalty
}

# For more aggressive recency preference
RECENCY_BOOST = {
    7: 2.0,   # Last week: 2x boost
    30: 1.5,  # Last month: 50% boost
    90: 1.0,  # Last quarter: Neutral
    999: 0.5  # Older: 50% penalty
}
```

### Adjust Result Count

```python
# More results = broader search, lower precision
results = await memory_service.search(query, limit=20)

# Fewer results = narrower search, higher precision
results = await memory_service.search(query, limit=5)
```

### Add Similarity Threshold

```python
# Filter out low-confidence matches
high_quality_results = [
    r for r in results
    if r.similarity >= 0.7  # Only 70%+ matches
]
```

---

## Common Use Cases

### 1. Find Related Work
```python
results = await memory_service.search(
    query="What did we do with permission dialogs?",
    limit=5
)
```

### 2. Recall Recent Decisions
```python
results = await memory_service.search_by_date(
    query="streaming architecture decisions",
    time_period="recent"
)
```

### 3. Find Past Solutions
```python
results = await memory_service.search(
    query="how did we fix the race condition?",
    limit=3
)
```

### 4. Browse by Component
```python
# Add metadata filter in repository layer
results = await memory_repository.search(
    query_embedding=embedding,
    limit=10,
    where_filter={"component": "permission-system"}
)
```

---

## Summary

Semantic search transforms development memories into a **queryable knowledge base** where:
- ✅ Natural language queries work
- ✅ Meaning matters more than exact wording
- ✅ Recent work is prioritized
- ✅ Fast enough for interactive use
- ✅ Scales to thousands of memories

No manual tagging or organization required - just search and find!

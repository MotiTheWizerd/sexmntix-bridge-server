# Caching Mechanism

## Overview

The embedding cache provides in-memory LRU (Least Recently Used) caching to dramatically reduce API calls and improve response times.

## Cache Architecture

```
┌─────────────────────────────────────────────────────┐
│            EmbeddingCache (Orchestrator)            │
│                                                     │
│  Public API:                                        │
│  • get(text, model) → embedding | None              │
│  • set(text, model, embedding)                      │
│  • stats() → CacheStats                             │
│  • clear()                                          │
└──────────────┬──────────────────────────────────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
    ↓          ↓          ↓
┌────────┐ ┌────────┐ ┌──────────┐
│  Key   │ │Storage │ │Expiration│
│Generator│ │Manager │ │ Handler  │
└────────┘ └────────┘ └──────────┘
    │          │          │
    ↓          ↓          ↓
┌─────────────────────────────────┐
│       CacheStorage              │
│  (Thread-safe dict operations)  │
│                                 │
│  {                              │
│    "key1": CacheEntry,          │
│    "key2": CacheEntry,          │
│    ...                          │
│  }                              │
└─────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────┐
│    EvictionStrategy (LRU)       │
└─────────────────────────────────┘
         │
         ↓
┌─────────────────────────────────┐
│       CacheMetrics              │
│  • hits: 850                    │
│  • misses: 150                  │
│  • hit_rate: 0.85               │
└─────────────────────────────────┘
```

## Cache Entry Structure

```python
@dataclass
class CacheEntry:
    key: str                    # Hash of text + model
    embedding: List[float]      # 768-dimensional vector
    timestamp: datetime         # When created
    last_accessed: datetime     # Last access time (for LRU)
    access_count: int           # Number of accesses
    model: str                  # Model name
    text_hash: str             # Original text hash (for debugging)
```

## Key Generation

### How Keys are Generated

```python
def generate_cache_key(text: str, model: str) -> str:
    # Combine text and model
    data = f"{text}|{model}"

    # SHA256 hash
    hash_full = hashlib.sha256(data.encode('utf-8')).hexdigest()

    # Truncate to 16 chars for readability
    key = hash_full[:16]

    return key
```

### Example

```
Text: "Fix authentication bug"
Model: "text-embedding-004"

Combined: "Fix authentication bug|text-embedding-004"

SHA256: "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6..."

Key: "a1b2c3d4e5f6g7h8"
```

### Why Hash?

1. **Fixed length**: All keys are 16 chars, regardless of text length
2. **Deterministic**: Same text + model → same key always
3. **Collision resistant**: SHA256 makes collisions extremely unlikely
4. **Fast lookup**: Dict lookup is O(1)

## Storage Operations

### Get Operation

```python
def get(text: str, model: str) -> Optional[List[float]]:
    # 1. Generate key
    key = generate_key(text, model)

    # 2. Check if key exists
    if key not in storage:
        metrics.record_miss()
        return None

    # 3. Get entry
    entry = storage[key]

    # 4. Check expiration
    age = now - entry.timestamp
    if age > TTL:
        # Expired - remove and return miss
        del storage[key]
        metrics.record_miss()
        return None

    # 5. Update LRU metadata
    entry.last_accessed = now
    entry.access_count += 1

    # 6. Record hit
    metrics.record_hit()

    return entry.embedding
```

**Time Complexity**: O(1)

### Set Operation

```python
def set(text: str, model: str, embedding: List[float]):
    # 1. Generate key
    key = generate_key(text, model)

    # 2. Check if cache is full
    if len(storage) >= MAX_SIZE and key not in storage:
        # Need to evict
        lru_key = find_lru_key()
        del storage[lru_key]

    # 3. Create entry
    entry = CacheEntry(
        key=key,
        embedding=embedding,
        timestamp=now,
        last_accessed=now,
        access_count=0,
        model=model,
        text_hash=hash(text)[:8]
    )

    # 4. Store
    storage[key] = entry
```

**Time Complexity**: O(n) worst case (LRU scan), typically O(1)

## LRU Eviction Strategy

### How LRU Works

When cache is full (1000 entries) and we need to add a new entry:

```python
def find_lru_key() -> str:
    # Find entry with oldest last_accessed time
    lru_entry = None
    lru_key = None

    for key, entry in storage.items():
        if lru_entry is None or entry.last_accessed < lru_entry.last_accessed:
            lru_entry = entry
            lru_key = key

    return lru_key
```

### Eviction Example

```
Cache state (size=3, max=3):
┌─────┬────────────┬──────────────────┐
│ Key │ Embedding  │ Last Accessed    │
├─────┼────────────┼──────────────────┤
│ A1  │ [...]      │ 10:00:00 ← LRU   │
│ B2  │ [...]      │ 10:05:00         │
│ C3  │ [...]      │ 10:10:00         │
└─────┴────────────┴──────────────────┘

New entry arrives (key=D4)
→ Cache full, need to evict
→ Find LRU: A1 (oldest last_accessed)
→ Remove A1
→ Add D4

New cache state:
┌─────┬────────────┬──────────────────┐
│ Key │ Embedding  │ Last Accessed    │
├─────┼────────────┼──────────────────┤
│ B2  │ [...]      │ 10:05:00         │
│ C3  │ [...]      │ 10:10:00         │
│ D4  │ [...]      │ 10:15:00 ← NEW   │
└─────┴────────────┴──────────────────┘
```

### Why LRU?

- **Temporal locality**: Recently accessed items likely to be accessed again
- **Simple**: Easy to understand and implement
- **Effective**: Good hit rates in practice (70-90%)

## TTL Expiration

### Time-Based Expiration

```python
TTL = 24 hours  # Default

def is_expired(entry: CacheEntry) -> bool:
    age = now - entry.timestamp
    return age > TTL
```

### Why 24 Hours?

1. **Embeddings are deterministic**: Same text → same embedding
2. **Model stability**: text-embedding-004 is stable (not retrained daily)
3. **Memory efficiency**: Prevents unbounded growth
4. **Fresh enough**: 24h is fresh for most use cases

### Expiration Check Points

Entries are checked for expiration at:
1. **Get operation**: Check before returning
2. **Background cleanup**: Periodic scan (every 1 hour)

### Background Cleanup

```python
def cleanup_expired():
    """Run periodically to remove expired entries"""
    now = datetime.now()
    expired_keys = []

    for key, entry in storage.items():
        if now - entry.timestamp > TTL:
            expired_keys.append(key)

    for key in expired_keys:
        del storage[key]

    logger.info(f"Removed {len(expired_keys)} expired entries")
```

## Cache Metrics

### Tracked Metrics

```python
@dataclass
class CacheMetrics:
    hits: int                   # Number of cache hits
    misses: int                 # Number of cache misses
    evictions: int              # Number of LRU evictions
    expirations: int            # Number of TTL expirations
    total_requests: int         # hits + misses
    hit_rate: float             # hits / total_requests
    current_size: int           # len(storage)
    max_size: int               # Configuration max
```

### Calculate Hit Rate

```python
def calculate_hit_rate() -> float:
    total = hits + misses
    if total == 0:
        return 0.0
    return hits / total
```

### Example Metrics Output

```python
stats = cache.stats()
# {
#     "hits": 8500,
#     "misses": 1500,
#     "evictions": 450,
#     "expirations": 200,
#     "total_requests": 10000,
#     "hit_rate": 0.85,
#     "current_size": 1000,
#     "max_size": 1000
# }
```

## Performance Analysis

### Cache Hit Scenarios

#### Scenario 1: Repeated Search Queries
```
Query 1: "authentication bug"  → MISS (300ms)
Query 2: "authentication bug"  → HIT (<1ms)
Query 3: "authentication bug"  → HIT (<1ms)

Speedup: 300x faster for repeated queries
```

#### Scenario 2: Similar Memories
```
Memory 1: "Fix login error"           → MISS
Memory 2: "Update user profile"       → MISS
Memory 3: "Fix login error"           → HIT (duplicate)
Memory 4: "Implement password reset"  → MISS
Memory 5: "Fix login error"           → HIT (duplicate again)

Hit rate: 40% (2/5)
Time saved: 2 * 300ms = 600ms
```

#### Scenario 3: Bulk Processing with Duplicates
```
Input: 10,000 texts
Unique texts: 7,000
Duplicates: 3,000

First pass:
- 7,000 MISS → API calls
- 3,000 HIT → from cache

Hit rate: 30%
API calls saved: 3,000
Cost saved: 3,000 * $0.0001 = $0.30
```

### Memory Footprint

Per entry size:
```
key: 16 chars              = 16 bytes
embedding: 768 floats      = 3,072 bytes (768 * 4)
timestamp: datetime        = 8 bytes
last_accessed: datetime    = 8 bytes
access_count: int          = 8 bytes
model: str (~20 chars)     = 20 bytes
text_hash: str (8 chars)   = 8 bytes
────────────────────────────────────
Total per entry:           ≈ 3,140 bytes ≈ 3 KB
```

Cache memory usage:
```
1,000 entries * 3 KB = 3 MB
```

**Conclusion**: Cache is very memory efficient.

## Configuration

### Environment Variables

```bash
# Cache size (number of entries)
EMBEDDING_CACHE_SIZE=1000

# TTL in hours
EMBEDDING_CACHE_TTL_HOURS=24

# Background cleanup interval (minutes)
EMBEDDING_CACHE_CLEANUP_INTERVAL=60

# Enable cache (for testing/debugging)
EMBEDDING_CACHE_ENABLED=true
```

### Tuning Recommendations

| Use Case | Cache Size | TTL | Rationale |
|----------|------------|-----|-----------|
| **Development** | 100 | 1h | Fast cache turnover for testing |
| **Production (low traffic)** | 1,000 | 24h | Default, good balance |
| **Production (high traffic)** | 5,000 | 24h | More unique queries |
| **Batch processing** | 10,000 | 1h | Many texts, short-lived |

### When to Increase Cache Size

Indicators that cache is too small:
1. **High eviction rate**: >50% of misses due to evictions
2. **Low hit rate**: <50% hit rate with repeated queries
3. **Frequent LRU churn**: Same entries evicted and re-added

### When to Decrease TTL

Indicators that TTL is too long:
1. **Memory pressure**: Running out of memory
2. **Stale embeddings**: Model updated but cache not refreshed
3. **One-time processing**: Texts won't be repeated

## Thread Safety

### Thread-Safe Operations

```python
import threading

class CacheStorage:
    def __init__(self):
        self._storage = {}
        self._lock = threading.RLock()

    def get(self, key: str) -> Optional[CacheEntry]:
        with self._lock:
            return self._storage.get(key)

    def set(self, key: str, entry: CacheEntry):
        with self._lock:
            self._storage[key] = entry

    def delete(self, key: str):
        with self._lock:
            if key in self._storage:
                del self._storage[key]
```

**Why Thread-Safe?**
- Multiple API requests may access cache concurrently
- Batch processing uses thread pool
- Background cleanup runs in separate thread

## Cache Warming

### Pre-populate Cache

For known frequent queries, pre-populate cache:

```python
def warm_cache(common_queries: List[str]):
    """Pre-generate embeddings for common queries"""
    for query in common_queries:
        # Generate and cache
        embedding_service.generate_embedding(query)

    logger.info(f"Warmed cache with {len(common_queries)} queries")
```

### When to Use

- Application startup
- After cache clear
- Before bulk processing with known queries

## Monitoring & Debugging

### Log Cache Performance

```python
# Log every 1000 requests
if metrics.total_requests % 1000 == 0:
    logger.info(
        f"Cache stats: hit_rate={metrics.hit_rate:.2%}, "
        f"size={metrics.current_size}/{metrics.max_size}"
    )
```

### Debugging Cache Misses

```python
# Enable debug logging
if cache_miss and logger.isEnabledFor(DEBUG):
    logger.debug(
        f"Cache miss: key={key[:8]}, "
        f"text_preview={text[:50]}, "
        f"model={model}"
    )
```

### Investigate Low Hit Rate

```bash
# Check cache stats
GET /embeddings/cache/stats

# Response:
{
  "hit_rate": 0.35,  # Low!
  "evictions": 850,  # High eviction rate
  "current_size": 1000,
  "max_size": 1000
}

# Diagnosis: Cache too small, increase size
```

## Best Practices

1. **Monitor hit rate**: Aim for >70%
2. **Size appropriately**: Balance memory vs hit rate
3. **Use batch processing**: Better cache utilization
4. **Warm cache**: Pre-populate for known queries
5. **Clear strategically**: Only clear when necessary (model change)

## Next Steps

- **Understand providers**: [Provider Architecture](./providers.md)
- **Component details**: [Key Components](./components.md)

---

*Part of the [Embedding Documentation](./README.md)*

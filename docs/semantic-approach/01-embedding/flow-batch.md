# Batch Embedding Generation Flow

## Overview

Batch processing allows efficient generation of multiple embeddings simultaneously using concurrency and cache optimization.

## When to Use Batch

| Scenario | Use Batch? | Reason |
|----------|-----------|--------|
| Migrating existing data | ✅ Yes | Process 100s-1000s of items efficiently |
| Bulk import | ✅ Yes | Concurrent API calls reduce total time |
| Real-time API request | ❌ No | Single embedding is faster for one item |
| Interactive search | ❌ No | User expects immediate response |

## Complete Batch Flow

```
┌────────────────────────────────────────────────────────┐
│ INPUT: ["text1", "text2", "text3", ..., "text100"]    │
└──────────────────────┬─────────────────────────────────┘
                       │
                       ↓
┌──────────────────────────────────────────────────────────┐
│ 1. BATCH VALIDATION                                      │
│    For each text:                                        │
│    ✓ Validate text                                       │
│    ✓ Generate cache key                                  │
│                                                          │
│    If any invalid → return error immediately            │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ↓
┌──────────────────────────────────────────────────────────┐
│ 2. CACHE PARTITION                                       │
│    Split into two lists:                                 │
│                                                          │
│    cached_items = []      # Items found in cache        │
│    uncached_items = []    # Items needing API call      │
│                                                          │
│    For each text:                                        │
│        if cache.has(key):                                │
│            cached_items.append((index, cached_embedding))│
│        else:                                             │
│            uncached_items.append((index, text))          │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ↓
┌──────────────────────────────────────────────────────────┐
│ 3. CONCURRENT API CALLS                                  │
│    BatchProcessor.process_concurrently()                 │
│                                                          │
│    ┌─────────────────────────────────────────┐          │
│    │  Thread Pool (10 concurrent workers)    │          │
│    │                                          │          │
│    │  Worker 1 → API call for text[0]        │          │
│    │  Worker 2 → API call for text[1]        │          │
│    │  Worker 3 → API call for text[2]        │          │
│    │  ...                                     │          │
│    │  Worker 10 → API call for text[9]       │          │
│    │                                          │          │
│    │  When worker finishes:                  │          │
│    │  → Pick next uncached text              │          │
│    │  → Make API call                        │          │
│    │  → Store in cache                       │          │
│    │  → Record result                        │          │
│    └─────────────────────────────────────────┘          │
│                                                          │
│    Max concurrent: 10                                    │
│    Timeout per request: 30s                              │
│    Retry per request: Up to 3 attempts                   │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ↓
┌──────────────────────────────────────────────────────────┐
│ 4. RESULT MERGING                                        │
│    Combine cached and API results:                       │
│                                                          │
│    results = [None] * len(texts)                         │
│                                                          │
│    # Fill in cached results                              │
│    for (index, embedding) in cached_items:               │
│        results[index] = EmbeddingResponse(               │
│            embedding=embedding,                          │
│            cached=True                                   │
│        )                                                 │
│                                                          │
│    # Fill in API results                                 │
│    for (index, embedding) in api_results:                │
│        results[index] = EmbeddingResponse(               │
│            embedding=embedding,                          │
│            cached=False                                  │
│        )                                                 │
│                                                          │
│    Preserve original order ✓                             │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ↓
┌──────────────────────────────────────────────────────────┐
│ 5. BATCH RESPONSE BUILDING                               │
│    EmbeddingBatchResponse {                              │
│        embeddings: List[EmbeddingResponse],              │
│        cache_hits: 75,                                   │
│        total_count: 100,                                 │
│        processing_time_seconds: 2.5,                     │
│        cache_hit_rate: 0.75                              │
│    }                                                     │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ↓
┌──────────────────────────────────────────────────────────┐
│ 6. EVENT EMISSION                                        │
│    Event: "embedding.batch_generated"                    │
│    Data: {                                               │
│        total_count: 100,                                 │
│        cache_hits: 75,                                   │
│        api_calls: 25,                                    │
│        processing_time_ms: 2500,                         │
│        avg_latency_ms: 100                               │
│    }                                                     │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ↓
┌──────────────────────────────────────────────────────────┐
│ OUTPUT: EmbeddingBatchResponse                           │
│         100 embeddings with cache statistics             │
└──────────────────────────────────────────────────────────┘
```

## Cache Optimization Strategy

### Example: 100 Texts

```
Input: 100 texts
Cache lookup: 0.1ms * 100 = 10ms

Results:
├─ 75 texts → CACHE HIT (no API call needed)
└─ 25 texts → CACHE MISS (need API call)

Concurrent API calls:
├─ Pool size: 10 workers
├─ Texts per worker: 25 / 10 = 2.5
└─ Total time: ~3 batches * 300ms = ~900ms

vs. Sequential (no batch):
└─ Total time: 25 * 300ms = 7500ms

Speedup: 8.3x faster
```

## Concurrency Model

### Thread Pool Architecture

```
┌─────────────────────────────────────────────────────┐
│           ThreadPoolExecutor (10 workers)           │
│                                                     │
│  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────┐           │
│  │Worker│  │Worker│  │Worker│  │Worker│  ...      │
│  │  1   │  │  2   │  │  3   │  │  4   │           │
│  └───┬──┘  └───┬──┘  └───┬──┘  └───┬──┘           │
│      │         │         │         │               │
└──────┼─────────┼─────────┼─────────┼───────────────┘
       │         │         │         │
       ↓         ↓         ↓         ↓
   ┌────────┬────────┬────────┬────────┐
   │ text10 │ text11 │ text12 │ text13 │  ...
   └────────┴────────┴────────┴────────┘
   Uncached texts queue

Each worker:
1. Picks next text from queue
2. Makes API call (with retry)
3. Stores result in cache
4. Returns embedding
5. Repeats until queue empty
```

### Concurrency Configuration

| Parameter | Value | Reason |
|-----------|-------|--------|
| **Max concurrent** | 10 | Balance speed vs API rate limits |
| **Request timeout** | 30s | Prevent hanging on slow requests |
| **Max retries** | 3 | Handle transient errors |
| **Backoff** | Exponential | Avoid overwhelming API on errors |

## Performance Comparison

### Example: 1000 Texts, 80% Cache Hit Rate

#### Sequential Processing
```
Cached (800):   800 * <1ms    = ~0.8s
Uncached (200): 200 * 300ms   = 60s
────────────────────────────────────
Total:                          ~61s
```

#### Batch Processing (10 concurrent)
```
Cached (800):   800 * <1ms    = ~0.8s
Uncached (200): 200 / 10      = 20 batches
                20 * 300ms    = ~6s
────────────────────────────────────
Total:                          ~7s

Speedup: 8.7x faster
```

#### Batch Processing (0% Cache Hit Rate)
```
All uncached:   1000 / 10     = 100 batches
                100 * 300ms   = 30s
────────────────────────────────────
Total:                          ~30s

vs Sequential:  1000 * 300ms  = 300s

Speedup: 10x faster
```

## Error Handling in Batch

### Partial Failure Strategy

**Default**: Fail fast (stop on first error)
```python
for text in uncached_texts:
    try:
        embedding = generate(text)
    except ProviderError:
        raise  # Stop entire batch
```

**Alternative**: Collect errors (continue on errors)
```python
results = []
errors = []

for index, text in uncached_texts:
    try:
        embedding = generate(text)
        results.append((index, embedding))
    except ProviderError as e:
        errors.append((index, str(e)))

# Return partial results + errors
return {
    "success": results,
    "errors": errors
}
```

### Retry Logic Per Item

Each uncached text has independent retry:
```python
def process_single(text):
    for attempt in range(3):
        try:
            return provider.generate_embedding(text)
        except RateLimitError:
            if attempt == 2:
                raise
            sleep(2 ** attempt)
        except ProviderError:
            raise  # Don't retry permanent errors
```

## Cache Impact Analysis

### High Cache Hit Rate (>70%)

**Scenario**: Processing recently stored memories
```
Input: 1000 texts
Cache hits: 850 (85%)
Cache misses: 150 (15%)

Time breakdown:
├─ Cache lookup:    1s  (1%)
├─ API calls:      4.5s (45%)
└─ Result merging:  0.5s (5%)

Total: ~6s
Cost: 150 API calls
```

### Low Cache Hit Rate (<30%)

**Scenario**: First-time bulk import
```
Input: 1000 texts
Cache hits: 100 (10%)
Cache misses: 900 (90%)

Time breakdown:
├─ Cache lookup:     1s  (3%)
├─ API calls:       27s (90%)
└─ Result merging:   0.5s (2%)

Total: ~28.5s
Cost: 900 API calls
```

**Optimization**: After first run, cache hit rate improves dramatically for similar texts.

## Batch Size Recommendations

| Batch Size | Cache Hit | Recommendation |
|------------|-----------|----------------|
| 1-10 | Any | Use single embedding (simpler) |
| 10-100 | <50% | Batch, 10 concurrent |
| 10-100 | >50% | Batch, excellent cache benefit |
| 100-1000 | Any | Batch, monitor API rate limits |
| 1000+ | Any | Split into multiple batches (100-500 each) |

## Memory Considerations

### Memory Usage Estimation

Per embedding: ~3KB (768 floats * 4 bytes)

| Batch Size | Memory Usage |
|------------|-------------|
| 100 | ~300 KB |
| 1,000 | ~3 MB |
| 10,000 | ~30 MB |
| 100,000 | ~300 MB |

**Recommendation**: For batches >10,000, process in chunks to avoid memory pressure.

## Code Example

```python
# Batch processing example
async def process_memory_migration(memories: List[Memory]):
    # Extract texts
    texts = [extract_searchable_text(m) for m in memories]

    # Generate embeddings (with caching and concurrency)
    batch_response = embedding_service.generate_batch(texts)

    # Log cache performance
    logger.info(f"Cache hit rate: {batch_response.cache_hit_rate:.1%}")
    logger.info(f"Processing time: {batch_response.processing_time_seconds:.1f}s")

    # Store in vector database
    for memory, embedding_resp in zip(memories, batch_response.embeddings):
        vector_repo.add_memory(
            id=memory.id,
            embedding=embedding_resp.embedding,
            document=memory.raw_data,
            metadata=extract_metadata(memory)
        )
```

## Monitoring Metrics

### Key Metrics to Track

1. **Cache hit rate**: Should be >70% for repeated processing
2. **Average latency**: Should be <50ms per embedding when cached
3. **Concurrent utilization**: Workers should be busy >80% of time
4. **Error rate**: Should be <1% with retries

### Sample Metrics Output

```json
{
  "batch_size": 1000,
  "cache_hits": 850,
  "cache_hit_rate": 0.85,
  "api_calls": 150,
  "processing_time_seconds": 6.2,
  "avg_latency_ms": 45,
  "errors": 0,
  "concurrent_workers": 10,
  "worker_utilization": 0.87
}
```

## Next Steps

- **Understand caching**: [Caching Mechanism](./caching.md)
- **Provider details**: [Provider Architecture](./providers.md)
- **Component reference**: [Key Components](./components.md)

---

*Part of the [Embedding Documentation](./README.md)*

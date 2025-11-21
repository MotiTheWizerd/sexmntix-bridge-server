# Single Embedding Generation Flow

## Overview

This document details how a single text input is converted into a 768-dimensional embedding vector.

## Complete Flow Diagram

```
┌──────────────────────────────────────────────────────────────┐
│ INPUT: "Fix authentication bug in login service"             │
└────────────────────────┬─────────────────────────────────────┘
                         │
                         ↓
┌────────────────────────────────────────────────────────────┐
│ 1. VALIDATION                                              │
│    TextValidator.validate(text)                            │
│                                                            │
│    Checks:                                                 │
│    ✓ Not empty                                             │
│    ✓ Valid UTF-8 encoding                                  │
│    ✓ Within length limits                                  │
│    ✓ No null bytes                                         │
│                                                            │
│    If invalid → raise ValidationError                      │
└────────────────────────┬───────────────────────────────────┘
                         │
                         ↓
┌────────────────────────────────────────────────────────────┐
│ 2. CACHE KEY GENERATION                                    │
│    KeyGenerator.generate(text, model)                      │
│                                                            │
│    key = SHA256(                                           │
│        text: "Fix authentication bug..."                   │
│        model: "text-embedding-004"                         │
│    )[:16]                                                  │
│                                                            │
│    Result: "a1b2c3d4e5f6g7h8"                             │
└────────────────────────┬───────────────────────────────────┘
                         │
                         ↓
┌────────────────────────────────────────────────────────────┐
│ 3. CACHE LOOKUP                                            │
│    CacheHandler.get(cache_key)                             │
│                                                            │
│    Checks:                                                 │
│    • Key exists in cache?                                  │
│    • Entry not expired? (< 24h old)                        │
└────────────────────────┬───────────────────────────────────┘
                         │
                ┌────────┴────────┐
                │                 │
           CACHE HIT         CACHE MISS
                │                 │
                ↓                 ↓
┌─────────────────────────────┐  ┌────────────────────────────┐
│ 4a. RETURN CACHED           │  │ 4b. PROVIDER API CALL      │
│     EmbeddingCache.get()    │  │     GoogleProvider         │
│                             │  │     .generate_embedding()  │
│     embedding: [768 floats] │  │                            │
│     cached: true            │  │  ┌──────────────────────┐ │
│     latency: <1ms           │  │  │ Request Builder      │ │
│                             │  │  │ Constructs payload:  │ │
│     Emit: cache_hit event   │  │  │ {                    │ │
└─────────────┬───────────────┘  │  │   "content": text,   │ │
              │                  │  │   "model": "...",    │ │
              │                  │  │   "task_type": "..." │ │
              │                  │  │ }                    │ │
              │                  │  └──────────┬───────────┘ │
              │                  │             ↓             │
              │                  │  ┌──────────────────────┐ │
              │                  │  │ HTTP Client          │ │
              │                  │  │ POST to:             │ │
              │                  │  │ generativelanguage   │ │
              │                  │  │   .googleapis.com    │ │
              │                  │  │                      │ │
              │                  │  │ Headers:             │ │
              │                  │  │ - API Key            │ │
              │                  │  │ - Content-Type       │ │
              │                  │  │                      │ │
              │                  │  │ Timeout: 30s         │ │
              │                  │  └──────────┬───────────┘ │
              │                  │             ↓             │
              │                  │  ┌──────────────────────┐ │
              │                  │  │ Retry Handler        │ │
              │                  │  │ Max retries: 3       │ │
              │                  │  │ Backoff: exponential │ │
              │                  │  │                      │ │
              │                  │  │ Retry on:            │ │
              │                  │  │ - 429 (rate limit)   │ │
              │                  │  │ - 500 (server error) │ │
              │                  │  │ - Network timeout    │ │
              │                  │  └──────────┬───────────┘ │
              │                  │             ↓             │
              │                  │  ┌──────────────────────┐ │
              │                  │  │ Response Parser      │ │
              │                  │  │ Extract embedding    │ │
              │                  │  │ from JSON response   │ │
              │                  │  │                      │ │
              │                  │  │ Response format:     │ │
              │                  │  │ {                    │ │
              │                  │  │   "embedding": {     │ │
              │                  │  │     "values": [...]  │ │
              │                  │  │   }                  │ │
              │                  │  │ }                    │ │
              │                  │  └──────────┬───────────┘ │
              │                  └─────────────┼─────────────┘
              │                                ↓
              │                  ┌────────────────────────────┐
              │                  │ 5. CACHE STORAGE           │
              │                  │    CacheHandler.set()      │
              │                  │                            │
              │                  │    Store:                  │
              │                  │    - key: "a1b2c3d4..."    │
              │                  │    - embedding: [768]      │
              │                  │    - timestamp: now        │
              │                  │                            │
              │                  │    If cache full:          │
              │                  │    → Evict LRU entry       │
              │                  └────────────┬───────────────┘
              │                               │
              └───────────────────────────────┘
                                              ↓
┌────────────────────────────────────────────────────────────┐
│ 6. RESPONSE BUILDING                                       │
│    ResponseBuilder.build()                                 │
│                                                            │
│    EmbeddingResponse {                                     │
│        embedding: [0.123, -0.456, 0.789, ... ] (768)      │
│        dimensions: 768                                     │
│        cached: true/false                                  │
│        model: "text-embedding-004"                         │
│        provider: "google"                                  │
│    }                                                       │
└────────────────────────┬───────────────────────────────────┘
                         │
                         ↓
┌────────────────────────────────────────────────────────────┐
│ 7. EVENT EMISSION                                          │
│    EventEmitter.emit()                                     │
│                                                            │
│    Event: "embedding.generated"                            │
│    Data: {                                                 │
│        text_length: 42,                                    │
│        cached: true/false,                                 │
│        latency_ms: 250,                                    │
│        provider: "google"                                  │
│    }                                                       │
└────────────────────────┬───────────────────────────────────┘
                         │
                         ↓
┌────────────────────────────────────────────────────────────┐
│ OUTPUT: EmbeddingResponse                                  │
│         768-dimensional vector ready for storage/search    │
└────────────────────────────────────────────────────────────┘
```

## Step-by-Step Walkthrough

### Step 1: Validation

**Purpose**: Ensure text is valid before processing

**Validation Checks**:
```python
# Check 1: Not empty
if not text or not text.strip():
    raise ValidationError("Text cannot be empty")

# Check 2: Valid encoding
try:
    text.encode('utf-8')
except UnicodeEncodeError:
    raise ValidationError("Invalid UTF-8 encoding")

# Check 3: Length limits
if len(text) > 10000:  # Example limit
    raise ValidationError("Text exceeds maximum length")

# Check 4: No null bytes
if '\x00' in text:
    raise ValidationError("Text contains null bytes")
```

**Why This Matters**: Invalid text can cause API errors or corrupt cache entries.

### Step 2: Cache Key Generation

**Purpose**: Create unique identifier for this text + model combination

**Key Generation**:
```python
# Combine text and model
data = f"{text}|{model}"

# Hash to fixed-length key
import hashlib
key = hashlib.sha256(data.encode()).hexdigest()[:16]
```

**Example**:
- Input: "Fix auth bug" + "text-embedding-004"
- Key: "a1b2c3d4e5f6g7h8"

**Why Hash?**: Same text always produces same key, enabling cache hits.

### Step 3: Cache Lookup

**Purpose**: Check if we already have this embedding

**Lookup Logic**:
```python
# 1. Check if key exists
if key not in cache:
    return None  # MISS

# 2. Check if expired
entry = cache[key]
age = now - entry.timestamp
if age > TTL:
    del cache[key]  # Remove stale entry
    return None  # MISS

# 3. Update LRU
cache.mark_accessed(key)

# 4. Return cached embedding
return entry.embedding  # HIT
```

**Performance Impact**:
- **Cache hit**: <1ms response time
- **Cache miss**: ~200-500ms (API call required)

### Step 4a: Return Cached (Cache Hit Path)

**Fast path** when embedding is already in cache:

```python
# Retrieve from cache
embedding = cache.get(key)

# Build response
response = EmbeddingResponse(
    embedding=embedding,
    dimensions=len(embedding),
    cached=True,  # Important: indicates cache hit
    model=model,
    provider="google"
)

# Emit cache hit event
emit_event("embedding.cache_hit", {
    "cache_key": key,
    "latency_ms": 0.5
})

return response
```

**Advantages**:
- Near-instant response
- No API cost
- No API rate limit concerns

### Step 4b: Provider API Call (Cache Miss Path)

**Slow path** when embedding must be generated:

#### 4b.1: Request Builder
```python
payload = {
    "content": text,
    "model": "models/text-embedding-004",
    "taskType": "SEMANTIC_SIMILARITY",
    "outputDimensionality": 768
}
```

#### 4b.2: HTTP Client
```python
response = requests.post(
    url="https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent",
    headers={
        "x-goog-api-key": api_key,
        "Content-Type": "application/json"
    },
    json=payload,
    timeout=30
)
```

#### 4b.3: Retry Handler
```python
for attempt in range(3):
    try:
        response = make_request()
        break
    except (RateLimitError, ServerError, Timeout):
        if attempt == 2:
            raise
        wait = 2 ** attempt  # 1s, 2s, 4s
        sleep(wait)
```

#### 4b.4: Response Parser
```python
# Parse JSON response
data = response.json()

# Extract embedding
embedding = data["embedding"]["values"]

# Validate dimensions
assert len(embedding) == 768
```

**Latency**: ~200-500ms depending on network and API load

### Step 5: Cache Storage

**Purpose**: Store embedding for future lookups

```python
# Create cache entry
entry = CacheEntry(
    key=key,
    embedding=embedding,
    timestamp=now,
    access_count=0
)

# Check if cache is full
if len(cache) >= MAX_SIZE:
    # Evict least recently used
    lru_key = find_lru()
    del cache[lru_key]

# Store in cache
cache[key] = entry
```

**Cache Policy**:
- **Size**: 1000 entries
- **TTL**: 24 hours
- **Eviction**: LRU (Least Recently Used)

### Step 6: Response Building

**Purpose**: Create standardized response object

```python
response = EmbeddingResponse(
    embedding=[0.123, -0.456, ...],  # 768 floats
    dimensions=768,
    cached=False,  # Was not cached
    model="text-embedding-004",
    provider="google"
)
```

**Response Fields**:
- `embedding`: The actual vector
- `dimensions`: Length of vector (768)
- `cached`: Whether result came from cache
- `model`: Model name used
- `provider`: Provider name (for multi-provider support)

### Step 7: Event Emission

**Purpose**: Notify observers and track metrics

```python
emit_event("embedding.generated", {
    "text_length": len(text),
    "cached": response.cached,
    "latency_ms": elapsed_time,
    "provider": "google",
    "cache_key": key
})
```

**Event Subscribers**:
- Metrics collection (Prometheus, etc.)
- Logging systems
- Monitoring dashboards

## Error Handling

### Validation Errors
```python
try:
    validate(text)
except ValidationError as e:
    return error_response(400, str(e))
```

### Provider Errors
```python
try:
    embedding = provider.generate_embedding(text)
except RateLimitError:
    return error_response(429, "Rate limit exceeded")
except ProviderError as e:
    return error_response(500, f"Provider error: {e}")
```

### Cache Errors
```python
try:
    cached = cache.get(key)
except CacheError as e:
    # Log error but continue without cache
    logger.warning(f"Cache error: {e}")
    cached = None
```

## Performance Metrics

### Timing Breakdown (Cache Miss)

| Stage | Time | % of Total |
|-------|------|------------|
| Validation | <1ms | <1% |
| Cache lookup | <1ms | <1% |
| API request | 200-400ms | ~90% |
| Response parsing | 5-10ms | ~3% |
| Cache storage | 2-5ms | ~2% |
| Response building | <1ms | <1% |
| Event emission | <1ms | <1% |
| **Total** | **~250ms** | **100%** |

### Timing Breakdown (Cache Hit)

| Stage | Time | % of Total |
|-------|------|------------|
| Validation | <1ms | ~20% |
| Cache lookup | <1ms | ~60% |
| Response building | <1ms | ~10% |
| Event emission | <1ms | ~10% |
| **Total** | **<1ms** | **100%** |

## Next Steps

- **Learn batch processing**: [Batch Flow](./flow-batch.md)
- **Understand caching**: [Caching Mechanism](./caching.md)
- **Provider details**: [Provider Architecture](./providers.md)

---

*Part of the [Embedding Documentation](./README.md)*

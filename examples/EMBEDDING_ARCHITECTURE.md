# Embedding Module Architecture

## Complete System Diagram

```
┌──────────────────────────────────────────────────────────────────────┐
│                         CLIENT APPLICATION                            │
│                     (Browser, CLI, VS Code Ext)                       │
└────────────────────────────┬─────────────────────────────────────────┘
                             │ HTTP/REST
                             ↓
┌──────────────────────────────────────────────────────────────────────┐
│                         API LAYER (FastAPI)                           │
├──────────────────────────────────────────────────────────────────────┤
│  POST   /embeddings          → create_embedding()                    │
│  POST   /embeddings/batch    → create_embeddings_batch()             │
│  GET    /embeddings/health   → health_check()                        │
│  GET    /embeddings/cache/stats → get_cache_stats()                  │
│  DELETE /embeddings/cache    → clear_cache()                         │
├──────────────────────────────────────────────────────────────────────┤
│  Dependencies:                                                        │
│  - get_embedding_service(request) → app.state.embedding_service      │
│  - get_logger(request) → app.state.logger                            │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             ↓
┌──────────────────────────────────────────────────────────────────────┐
│                    SERVICE LAYER (Business Logic)                     │
├──────────────────────────────────────────────────────────────────────┤
│  EmbeddingService (extends BaseService)                              │
│                                                                       │
│  Methods:                                                             │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ generate_embedding(text) → EmbeddingResponse                │    │
│  │   1. Validate text                                          │    │
│  │   2. Check cache (if enabled)                               │    │
│  │   3. Generate via provider (if cache miss)                  │    │
│  │   4. Store in cache                                         │    │
│  │   5. Publish event                                          │    │
│  │   6. Return response                                        │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ generate_embeddings_batch(texts) → BatchResponse           │    │
│  │   1. Validate texts list                                    │    │
│  │   2. Check cache for each text                              │    │
│  │   3. Generate uncached texts in batches                     │    │
│  │   4. Cache new embeddings                                   │    │
│  │   5. Publish batch event                                    │    │
│  │   6. Return combined results                                │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  Dependencies:                                                        │
│  - provider: BaseEmbeddingProvider                                   │
│  - cache: EmbeddingCache                                             │
│  - event_bus: EventBus                                               │
│  - logger: Logger                                                    │
└────────────────┬──────────────────────┬──────────────────────────────┘
                 │                      │
                 ↓                      ↓
┌────────────────────────────┐  ┌─────────────────────────────────────┐
│   CACHE LAYER              │  │    EVENT BUS                        │
├────────────────────────────┤  ├─────────────────────────────────────┤
│  EmbeddingCache            │  │  Publishes:                         │
│                            │  │  - embedding.generated              │
│  • LRU eviction            │  │  - embedding.batch_generated        │
│  • TTL expiration (24h)    │  │  - embedding.cache_hit              │
│  • Hash-based keys         │  │  - embedding.error                  │
│  • Hit/miss tracking       │  │  - embedding.health_check           │
│  • Max 1000 entries        │  │                                     │
│                            │  │  Subscribers can listen and react   │
│  Methods:                  │  └─────────────────────────────────────┘
│  - get(text, model)        │
│  - set(text, model, emb)   │
│  - get_stats()             │
│  - clear()                 │
└────────────────────────────┘
                 │
                 ↓
┌──────────────────────────────────────────────────────────────────────┐
│                    PROVIDER LAYER (External APIs)                     │
├──────────────────────────────────────────────────────────────────────┤
│  BaseEmbeddingProvider (Abstract)                                    │
│  ├── generate_embedding(text) → List[float]                          │
│  ├── generate_embeddings_batch(texts) → List[List[float]]            │
│  └── health_check() → bool                                           │
│                                                                       │
│  GoogleEmbeddingProvider (Implementation)                            │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │ API: https://generativelanguage.googleapis.com/v1beta       │    │
│  │ Model: models/text-embedding-004                            │    │
│  │ Output: 768-dimensional vector                              │    │
│  │                                                             │    │
│  │ Features:                                                   │    │
│  │ • Async HTTP client (httpx)                                 │    │
│  │ • Retry logic (3 attempts, exponential backoff)             │    │
│  │ • Timeout handling (30s)                                    │    │
│  │ • Rate limit detection (429 response)                       │    │
│  │ • Connection error recovery                                 │    │
│  │ • Batch processing (10 concurrent)                          │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                       │
│  Future Providers:                                                   │
│  ├── OpenAIEmbeddingProvider                                         │
│  ├── CohereEmbeddingProvider                                         │
│  └── LocalEmbeddingProvider (sentence-transformers)                  │
└────────────────────────────┬─────────────────────────────────────────┘
                             │
                             ↓
┌──────────────────────────────────────────────────────────────────────┐
│                    EXTERNAL SERVICES                                  │
├──────────────────────────────────────────────────────────────────────┤
│  Google Generative AI API                                            │
│  • text-embedding-004 model                                          │
│  • ~$0.00001 per 1000 characters                                     │
│  • ~100-300ms latency                                                │
│  • Generous free tier                                                │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Data Flow: Single Embedding Request

```
1. CLIENT REQUEST
   POST /embeddings
   {"text": "permission dialog UI redesign"}
        │
        ↓
2. API LAYER (routes/embeddings.py)
   ├── Validate request (Pydantic: EmbeddingCreate)
   ├── Inject dependencies (service, logger)
   └── Call: embedding_service.generate_embedding(text)
        │
        ↓
3. SERVICE LAYER (service.py)
   ├── Validate text (non-empty)
   ├── Check cache: cache.get(text, model)
   │
   ├─── CACHE HIT ────────────────────────┐
   │    Return cached embedding            │
   │    Publish: embedding.cache_hit       │
   │                                       │
   └─── CACHE MISS ──────────────────┐    │
        │                            │    │
        ↓                            │    │
4. PROVIDER LAYER (provider.py)      │    │
   ├── Prepare request payload       │    │
   ├── HTTP POST to Google API       │    │
   ├── Retry on failure (3x)         │    │
   ├── Parse response                │    │
   └── Return: List[float] (768D)    │    │
        │                            │    │
        ↓                            │    │
5. SERVICE LAYER (continued)         │    │
   ├── Cache embedding ──────────────┘    │
   ├── Create EmbeddingResponse           │
   ├── Publish: embedding.generated       │
   └── Return response ───────────────────┘
        │
        ↓
6. API LAYER (response)
   ├── Format as JSON (Pydantic)
   └── Return 201 Created
        │
        ↓
7. CLIENT RECEIVES
   {
     "text": "permission dialog UI redesign",
     "embedding": [0.023, -0.123, ...],
     "model": "models/text-embedding-004",
     "provider": "google",
     "dimensions": 768,
     "cached": false,
     "generated_at": "2025-11-12T10:30:00Z"
   }
```

---

## Data Flow: Batch Embedding Request

```
1. CLIENT REQUEST
   POST /embeddings/batch
   {"texts": ["text1", "text2", "text3"]}
        │
        ↓
2. SERVICE LAYER
   ├── For each text:
   │   ├── Check cache
   │   └── If cache miss → add to batch
   │
   ├── Cache hits: 1/3 ──────┐
   └── Need to generate: 2/3 │
        │                    │
        ↓                    │
3. PROVIDER LAYER            │
   ├── Split into batches    │
   ├── Process 10 concurrent │
   └── Return embeddings     │
        │                    │
        ↓                    │
4. SERVICE LAYER             │
   ├── Cache new embeddings  │
   ├── Combine with cache ←──┘
   ├── Calculate stats
   └── Return BatchResponse
```

---

## Component Interactions

```
┌─────────────────────────────────────────────────────────────────┐
│                        APP INITIALIZATION                        │
│  (app.py - Startup)                                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. Load environment variables (.env)                           │
│     GOOGLE_API_KEY, EMBEDDING_MODEL, CACHE_SIZE, etc.          │
│                                                                 │
│  2. Create ProviderConfig                                       │
│     ProviderConfig(                                             │
│       provider_name="google",                                   │
│       model="models/text-embedding-004",                        │
│       api_key=GOOGLE_API_KEY,                                   │
│       timeout=30.0,                                             │
│       max_retries=3                                             │
│     )                                                           │
│                                                                 │
│  3. Initialize GoogleEmbeddingProvider                          │
│     provider = GoogleEmbeddingProvider(config)                  │
│                                                                 │
│  4. Initialize EmbeddingCache                                   │
│     cache = EmbeddingCache(                                     │
│       max_size=1000,                                            │
│       ttl_hours=24                                              │
│     )                                                           │
│                                                                 │
│  5. Create EmbeddingService                                     │
│     service = EmbeddingService(                                 │
│       event_bus=event_bus,                                      │
│       logger=logger,                                            │
│       provider=provider,                                        │
│       cache=cache,                                              │
│       cache_enabled=True                                        │
│     )                                                           │
│                                                                 │
│  6. Attach to app.state                                         │
│     app.state.embedding_service = service                       │
│                                                                 │
│  7. Register routes                                             │
│     app.include_router(embeddings.router)                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## Dependency Injection Flow

```
FastAPI Request
     │
     ↓
Route Handler
     │
     ├── Depends(get_embedding_service)
     │        │
     │        ├── request.app.state.embedding_service
     │        │        │
     │        │        └── EmbeddingService instance
     │        │                 │
     │        │                 ├── provider: GoogleEmbeddingProvider
     │        │                 ├── cache: EmbeddingCache
     │        │                 ├── event_bus: EventBus
     │        │                 └── logger: Logger
     │        │
     │        └── Returns: EmbeddingService
     │
     └── Depends(get_logger)
              │
              └── request.app.state.logger
                       │
                       └── Logger instance
```

---

## Error Handling Flow

```
Request → Service → Provider → Google API
                         │
                         ├── Network Error
                         │   ├── Retry #1 (wait 1s)
                         │   ├── Retry #2 (wait 2s)
                         │   ├── Retry #3 (wait 4s)
                         │   └── Raise: ProviderConnectionError
                         │
                         ├── Timeout
                         │   ├── Retry with backoff
                         │   └── Raise: ProviderTimeoutError
                         │
                         ├── Rate Limit (429)
                         │   └── Raise: APIRateLimitError
                         │              (with retry_after)
                         │
                         └── HTTP Error
                             └── Raise: ProviderError

Service catches exceptions:
     ├── Publishes: embedding.error event
     ├── Logs error details
     └── Re-raises for API layer

API Layer:
     ├── Catches InvalidTextError → 400
     ├── Catches ProviderError → 503
     └── Catches Exception → 500
```

---

## Cache Architecture

```
┌────────────────────────────────────────────────────────────┐
│              EmbeddingCache (In-Memory LRU)                │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  Storage:                                                  │
│  ┌──────────────────────────────────────────────────┐    │
│  │ _cache: Dict[key, CacheEntry]                    │    │
│  │                                                  │    │
│  │ Key: SHA256(model + text)                        │    │
│  │   Example: "a3b2c1d4..."                         │    │
│  │                                                  │    │
│  │ Value: {                                         │    │
│  │   "embedding": [0.023, -0.123, ...],             │    │
│  │   "cached_at": datetime,                         │    │
│  │   "text_preview": "permission dialog..."         │    │
│  │ }                                                │    │
│  └──────────────────────────────────────────────────┘    │
│                                                            │
│  Access Tracking:                                         │
│  ┌──────────────────────────────────────────────────┐    │
│  │ _access_times: Dict[key, datetime]               │    │
│  │                                                  │    │
│  │ Used for LRU eviction                            │    │
│  └──────────────────────────────────────────────────┘    │
│                                                            │
│  Metrics:                                                 │
│  ├── _hit_count: int                                      │
│  ├── _miss_count: int                                     │
│  └── hit_rate: (hits / total) * 100                       │
│                                                            │
│  Operations:                                              │
│  ├── get(text, model) → embedding | None                  │
│  │   1. Generate key                                      │
│  │   2. Check existence                                   │
│  │   3. Check TTL                                         │
│  │   4. Update access time                                │
│  │   5. Return embedding                                  │
│  │                                                        │
│  ├── set(text, model, embedding)                          │
│  │   1. Evict oldest if full                              │
│  │   2. Store embedding                                   │
│  │   3. Record access time                                │
│  │                                                        │
│  └── get_stats() → Dict                                   │
│      Returns: size, max_size, hit_rate, etc.              │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

---

## Event Publishing System

```
┌─────────────────────────────────────────────────────────────┐
│                      EventBus                               │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  EmbeddingService publishes:                                │
│                                                             │
│  ┌───────────────────────────────────────────────────┐     │
│  │ embedding.generated                               │     │
│  │ {                                                 │     │
│  │   "text_preview": "permission dialog...",         │     │
│  │   "model": "models/text-embedding-004",           │     │
│  │   "provider": "google",                           │     │
│  │   "dimensions": 768,                              │     │
│  │   "duration_seconds": 0.234,                      │     │
│  │   "cached": false                                 │     │
│  │ }                                                 │     │
│  └───────────────────────────────────────────────────┘     │
│                                                             │
│  ┌───────────────────────────────────────────────────┐     │
│  │ embedding.cache_hit                               │     │
│  │ {                                                 │     │
│  │   "text_preview": "...",                          │     │
│  │   "model": "...",                                 │     │
│  │   "dimensions": 768                               │     │
│  │ }                                                 │     │
│  └───────────────────────────────────────────────────┘     │
│                                                             │
│  ┌───────────────────────────────────────────────────┐     │
│  │ embedding.batch_generated                         │     │
│  │ {                                                 │     │
│  │   "total_count": 10,                              │     │
│  │   "cache_hits": 3,                                │     │
│  │   "newly_generated": 7,                           │     │
│  │   "processing_time_seconds": 1.234,               │     │
│  │   "model": "...",                                 │     │
│  │   "provider": "google"                            │     │
│  │ }                                                 │     │
│  └───────────────────────────────────────────────────┘     │
│                                                             │
│  Subscribers can:                                           │
│  ├── Log metrics to monitoring                              │
│  ├── Track usage for billing                                │
│  ├── Trigger webhooks                                       │
│  └── Update analytics dashboards                            │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Integration with Memory System

```
┌─────────────────────────────────────────────────────────────┐
│                    MEMORY CREATION FLOW                      │
└─────────────────────────────────────────────────────────────┘

POST /mental-notes or /memory-logs
     │
     ↓
┌─────────────────────────────────────────────────────────────┐
│  1. Create memory object                                    │
│     memory = MentalNote(                                    │
│       task="permission-dialog-redesign",                    │
│       summary="Complete redesign with dark theme",          │
│       ...                                                   │
│     )                                                       │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│  2. Prepare embedding text                                  │
│     text = f"""                                             │
│       Date: {memory.date}                                   │
│       Task: {memory.task}                                   │
│       Component: {memory.component}                         │
│       Summary: {memory.summary}                             │
│       Tags: {', '.join(memory.tags)}                        │
│       Root Cause: {memory.root_cause}                       │
│       Solution: {memory.solution}                           │
│     """                                                     │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│  3. Generate embedding                                      │
│     embedding = await embedding_service.generate_embedding( │
│       text=text                                             │
│     )                                                       │
│     # Returns: EmbeddingResponse with 768D vector           │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│  4. Store in ChromaDB                                       │
│     collection.add(                                         │
│       ids=[memory.id],                                      │
│       embeddings=[embedding.embedding],                     │
│       documents=[memory.model_dump_json()],                 │
│       metadatas={                                           │
│         "task": memory.task,                                │
│         "date": memory.date,                                │
│         "component": memory.component                       │
│       }                                                     │
│     )                                                       │
│     collection.count()  # Force index rebuild               │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│  5. Return success                                          │
│     HTTP 201 Created                                        │
└─────────────────────────────────────────────────────────────┘


┌─────────────────────────────────────────────────────────────┐
│                    SEMANTIC SEARCH FLOW                      │
└─────────────────────────────────────────────────────────────┘

GET /mental-notes/search?q=permission+dialog
     │
     ↓
┌─────────────────────────────────────────────────────────────┐
│  1. Generate query embedding                                │
│     query_emb = await embedding_service.generate_embedding( │
│       text="permission dialog issues"                       │
│     )                                                       │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│  2. Search ChromaDB                                         │
│     results = collection.query(                             │
│       query_embeddings=[query_emb.embedding],               │
│       n_results=10,                                         │
│       where={"date": {"$gte": "2025-11-01"}}                │
│     )                                                       │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│  3. Apply recency boost                                     │
│     # Boost recent memories for relevance                   │
└────────────────────┬────────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────────┐
│  4. Return ranked results                                   │
│     HTTP 200 OK                                             │
│     [                                                       │
│       {memory: {...}, similarity: 0.884},                   │
│       {memory: {...}, similarity: 0.762},                   │
│       ...                                                   │
│     ]                                                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Summary

This architecture provides:

✅ **Clean separation of concerns** - Each layer has a single responsibility
✅ **Provider abstraction** - Easy to swap embedding providers
✅ **Caching optimization** - Reduces API costs and latency
✅ **Event-driven monitoring** - Track all operations via events
✅ **Error resilience** - Automatic retries and graceful degradation
✅ **Type safety** - Full Pydantic validation throughout
✅ **Scalability** - Ready for batch processing and high volume
✅ **Integration-ready** - Designed for memory system integration

The module follows your existing patterns and is production-ready for semantic search implementation.

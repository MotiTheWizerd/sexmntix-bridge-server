# Embedding Generation Module

## Overview

The embedding module converts text into numerical vectors (embeddings) that capture semantic meaning. This enables similarity-based search where "login error" and "authentication failure" are understood as related concepts.

## What You'll Learn

This section covers:
- [File Structure](./file-structure.md) - Module organization
- [Single Embedding Flow](./flow-single.md) - How one text becomes a vector
- [Batch Embedding Flow](./flow-batch.md) - Processing multiple texts efficiently
- [Caching Mechanism](./caching.md) - Performance optimization via LRU cache
- [Provider Architecture](./providers.md) - Pluggable embedding providers
- [Key Components](./components.md) - Core classes and their responsibilities

## Quick Facts

| Aspect | Details |
|--------|---------|
| **Current Provider** | Google text-embedding-004 |
| **Dimensions** | 768 |
| **Cache Strategy** | LRU (1000 items, 24h TTL) |
| **Batch Concurrency** | 10 concurrent requests |
| **Average Latency** | ~200-500ms (cold), <1ms (cached) |

## Core Workflow

```
Text Input
    ↓
Validation (non-empty, proper encoding)
    ↓
Cache Check (text + model hash)
    ↓
├─ HIT → Return cached [fast]
│
└─ MISS → Provider API call [slow]
           ↓
           Store in cache
           ↓
           Return embedding
```

## Use Cases

### 1. Memory Storage
When storing a new memory log:
```python
# Extract searchable text from memory
text = extract_searchable_text(memory_log)

# Generate embedding
embedding = embedding_service.generate_embedding(text)

# Store in vector database
vector_repo.add_memory(id, embedding, document, metadata)
```

### 2. Search Queries
When searching for similar memories:
```python
# Convert query to embedding
query_embedding = embedding_service.generate_embedding("auth bug fix")

# Search for similar vectors
results = vector_repo.search(query_embedding, limit=10)
```

### 3. Batch Processing
When migrating existing data:
```python
# Process multiple texts at once
texts = [memory.text for memory in memories]
batch_response = embedding_service.generate_batch(texts)

# Returns embeddings with cache stats
for i, embedding_resp in enumerate(batch_response.embeddings):
    store_embedding(memories[i].id, embedding_resp.embedding)
```

## Key Features

### Provider Abstraction
Switch embedding providers without changing application code:
```python
# Easy to swap providers
class OpenAIProvider(EmbeddingProvider):
    def generate_embedding(self, text: str) -> List[float]:
        # OpenAI implementation
        pass

# Or use custom models
class CustomModelProvider(EmbeddingProvider):
    def generate_embedding(self, text: str) -> List[float]:
        # Your model implementation
        pass
```

### Automatic Caching
Cache is transparent and automatic:
- First call: API request (~300ms)
- Second call with same text: Cache hit (<1ms)
- Saves cost and improves performance

### Error Handling
Robust retry logic with exponential backoff:
- Transient errors: Automatic retry (up to 3 attempts)
- Rate limits: Exponential backoff
- Permanent errors: Propagate with clear error messages

### Observability
Events emitted for monitoring:
- `embedding.generated` - Successful generation
- `embedding.cache_hit` - Cache hit occurred
- `embedding.error` - Error during generation

## Configuration

Key environment variables:
```bash
# Google API
GOOGLE_API_KEY=your_key_here

# Cache settings (optional, defaults shown)
EMBEDDING_CACHE_SIZE=1000
EMBEDDING_CACHE_TTL_HOURS=24

# Batch settings
EMBEDDING_BATCH_CONCURRENCY=10
```

## Performance Considerations

### When to Use Batch
- **Use batch**: Migrating data, bulk processing
- **Use single**: Real-time API calls, interactive search

### Cache Hit Rate
Monitor cache effectiveness:
```python
stats = embedding_service.get_cache_stats()
# {
#   "hits": 850,
#   "misses": 150,
#   "hit_rate": 0.85,
#   "size": 1000
# }
```

Good hit rate: >70%
If hit rate is low, consider increasing cache size.

### Cost Optimization
- **Caching**: Reduces API calls by 70-90% in typical usage
- **Batch processing**: More efficient than individual calls
- **Text deduplication**: Check cache before generating

## Next Steps

- **Understand structure**: [File Structure](./file-structure.md)
- **Follow the flow**: [Single Embedding Flow](./flow-single.md)
- **Optimize performance**: [Caching Mechanism](./caching.md)
- **Add new provider**: [Provider Architecture](./providers.md)

---

*Part of the [Semantic Approach Documentation](../README.md)*

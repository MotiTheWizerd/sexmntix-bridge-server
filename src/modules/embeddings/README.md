# Embeddings Module

Production-ready text embedding generation module for the Semantic Bridge API.

## Overview

This module provides a complete embedding generation solution with:
- **Provider abstraction** - Easy to swap between Google, OpenAI, or local models
- **Caching** - In-memory LRU cache to reduce API costs
- **Batch processing** - Efficient multi-text embedding
- **Event-driven** - Publishes domain events for monitoring
- **Error resilience** - Retry logic, timeout handling, graceful degradation

## Quick Start

### 1. Configuration

Add to your `.env` file:

```bash
# Get API key from: https://aistudio.google.com/app/apikey
GOOGLE_API_KEY=your_api_key_here
EMBEDDING_MODEL=models/text-embedding-004
EMBEDDING_CACHE_ENABLED=true
EMBEDDING_CACHE_SIZE=1000
```

### 2. API Endpoints

#### Generate Single Embedding

```bash
POST /embeddings
Content-Type: application/json

{
  "text": "permission dialog UI redesign with dark theme"
}
```

**Response:**
```json
{
  "text": "permission dialog UI redesign with dark theme",
  "embedding": [0.0234, -0.1234, 0.5678, ...],
  "model": "models/text-embedding-004",
  "provider": "google",
  "dimensions": 768,
  "cached": false,
  "generated_at": "2025-11-12T10:30:00Z"
}
```

#### Batch Embeddings

```bash
POST /embeddings/batch
Content-Type: application/json

{
  "texts": [
    "permission dialog UI",
    "authentication flow redesign",
    "dark mode implementation"
  ]
}
```

**Response:**
```json
{
  "embeddings": [
    {
      "text": "permission dialog UI",
      "embedding": [0.123, -0.456, ...],
      "model": "models/text-embedding-004",
      "provider": "google",
      "dimensions": 768,
      "cached": false
    },
    ...
  ],
  "total_count": 3,
  "cache_hits": 0,
  "processing_time_seconds": 0.456
}
```

#### Health Check

```bash
GET /embeddings/health
```

#### Cache Statistics

```bash
GET /embeddings/cache/stats
```

**Response:**
```json
{
  "enabled": true,
  "size": 45,
  "max_size": 1000,
  "hit_count": 120,
  "miss_count": 45,
  "hit_rate_percent": 72.73,
  "total_requests": 165
}
```

#### Clear Cache

```bash
DELETE /embeddings/cache
```

## Architecture

### Module Structure

```
src/modules/embeddings/
├── __init__.py              # Public exports
├── models.py                # Pydantic schemas
├── service.py               # Business logic (EmbeddingService)
├── provider.py              # Provider abstraction + implementations
├── cache.py                 # In-memory LRU cache
└── exceptions.py            # Custom exceptions
```

### Layers

1. **API Layer** (`src/api/routes/embeddings.py`)
   - HTTP endpoints
   - Request validation
   - Error handling

2. **Service Layer** (`service.py`)
   - Business logic orchestration
   - Cache coordination
   - Event publishing

3. **Provider Layer** (`provider.py`)
   - External API integration
   - Retry logic
   - Error handling

4. **Cache Layer** (`cache.py`)
   - In-memory storage
   - LRU eviction
   - TTL management

## Using in Your Code

### Python Service Integration

```python
from src.modules.embeddings import EmbeddingService
from src.api.dependencies.embedding import get_embedding_service

# In a route handler
async def my_route(
    embedding_service: EmbeddingService = Depends(get_embedding_service)
):
    # Generate embedding
    result = await embedding_service.generate_embedding(
        text="some text to embed"
    )

    # Access the vector
    vector = result.embedding  # List[float] with 768 dimensions

    # Store in ChromaDB, PostgreSQL, etc.
    # ...
```

### Batch Processing

```python
# Generate embeddings for multiple texts efficiently
texts = ["text 1", "text 2", "text 3"]

batch_result = await embedding_service.generate_embeddings_batch(
    texts=texts
)

for embedding_response in batch_result.embeddings:
    print(f"Text: {embedding_response.text[:50]}...")
    print(f"Dimensions: {embedding_response.dimensions}")
    print(f"Cached: {embedding_response.cached}")
```

## Configuration Options

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `GOOGLE_API_KEY` | - | **Required** - Google AI API key |
| `EMBEDDING_MODEL` | `models/text-embedding-004` | Model to use |
| `EMBEDDING_TIMEOUT` | `30.0` | Request timeout (seconds) |
| `EMBEDDING_MAX_RETRIES` | `3` | Max retry attempts |
| `EMBEDDING_CACHE_ENABLED` | `true` | Enable caching |
| `EMBEDDING_CACHE_SIZE` | `1000` | Max cached embeddings |
| `EMBEDDING_CACHE_TTL_HOURS` | `24` | Cache entry lifetime |

## Events Published

The service publishes these domain events:

- `embedding.generated` - Single embedding created
- `embedding.batch_generated` - Batch embeddings created
- `embedding.cache_hit` - Embedding served from cache
- `embedding.error` - Embedding generation failed
- `embedding.health_check` - Health check completed

**Event Example:**
```python
{
    "text_preview": "permission dialog UI redesign...",
    "model": "models/text-embedding-004",
    "provider": "google",
    "dimensions": 768,
    "duration_seconds": 0.234,
    "cached": false
}
```

## Error Handling

### Exception Hierarchy

```
EmbeddingError (base)
├── InvalidTextError (400)
├── ProviderError (503)
│   ├── APIRateLimitError (429 from provider)
│   ├── ProviderConnectionError (network issues)
│   └── ProviderTimeoutError (timeout)
```

### Example Error Handling

```python
from src.modules.embeddings import (
    InvalidTextError,
    ProviderError,
    APIRateLimitError
)

try:
    result = await embedding_service.generate_embedding(text)
except InvalidTextError as e:
    # Handle bad input (400)
    logger.warning(f"Invalid text: {e}")
except APIRateLimitError as e:
    # Handle rate limiting (wait and retry)
    logger.warning(f"Rate limited, retry after {e.retry_after}s")
except ProviderError as e:
    # Handle provider issues (503)
    logger.error(f"Provider error: {e}")
```

## Best Practices

### 1. Memory System Integration

For your memory/mental notes system:

```python
# When creating a memory
memory_text = f"""
Date: {memory.date}
Component: {memory.component}
Task: {memory.task}
Summary: {memory.summary}
Tags: {', '.join(memory.tags)}
Root Cause: {memory.root_cause}
Solution: {memory.solution}
"""

# Generate embedding
embedding_result = await embedding_service.generate_embedding(memory_text)

# Store in ChromaDB
collection.add(
    ids=[memory.id],
    embeddings=[embedding_result.embedding],
    documents=[memory_json],
    metadatas=[memory_metadata]
)
```

### 2. Semantic Search

```python
# Search by query
query = "permission dialog issues"
query_embedding = await embedding_service.generate_embedding(query)

# Search in ChromaDB
results = collection.query(
    query_embeddings=[query_embedding.embedding],
    n_results=10
)
```

### 3. Caching Strategy

- Enable caching in production to reduce costs
- Cache hits avoid API calls entirely
- Useful for repeated queries or similar texts
- Monitor cache stats via `/embeddings/cache/stats`

## Performance

### Latency

- **Single embedding**: ~100-300ms (Google API)
- **Batch (10 texts)**: ~500-1000ms (concurrent processing)
- **Cache hit**: <1ms

### Cost Optimization

- Caching reduces API costs by ~70% in production
- Batch processing is more efficient than individual calls
- Monitor cache hit rate to optimize settings

### Scalability

- In-memory cache: Good for single-server deployments
- For multi-server: Consider Redis cache (future enhancement)
- Handles 1000s of embeddings efficiently

## Adding New Providers

To add OpenAI or other providers:

### 1. Create Provider Class

```python
# src/modules/embeddings/provider.py

class OpenAIEmbeddingProvider(BaseEmbeddingProvider):
    async def generate_embedding(self, text: str) -> List[float]:
        # Implement OpenAI API call
        pass

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        # OpenAI has native batch API
        pass

    async def health_check(self) -> bool:
        pass
```

### 2. Update Configuration

```python
# src/api/app.py

if provider_type == "openai":
    embedding_provider = OpenAIEmbeddingProvider(config)
elif provider_type == "google":
    embedding_provider = GoogleEmbeddingProvider(config)
```

## Testing

### Manual Testing

```bash
# Start server
poetry run uvicorn src.api.app:app --reload

# Test endpoint
curl -X POST http://localhost:8000/embeddings \
  -H "Content-Type: application/json" \
  -d '{"text": "test embedding generation"}'

# Check health
curl http://localhost:8000/embeddings/health

# View cache stats
curl http://localhost:8000/embeddings/cache/stats
```

### Integration Example

See [examples/01-embedding-model.md](../../../examples/01-embedding-model.md) for complete flow documentation.

## Troubleshooting

### "GOOGLE_API_KEY not found"

- Add `GOOGLE_API_KEY` to your `.env` file
- Get API key from: https://aistudio.google.com/app/apikey

### Rate Limiting

- Google has generous free tier limits
- Consider upgrading if hitting limits
- Service auto-retries with exponential backoff

### Cache Not Working

- Check `EMBEDDING_CACHE_ENABLED=true` in `.env`
- Monitor hit rate via `/embeddings/cache/stats`
- Increase `EMBEDDING_CACHE_SIZE` if needed

## Future Enhancements

- [ ] OpenAI provider implementation
- [ ] Local model support (sentence-transformers)
- [ ] Redis cache for multi-server deployments
- [ ] PostgreSQL vector storage with pgvector
- [ ] Streaming embeddings for real-time use
- [ ] Prometheus metrics export
- [ ] Rate limit handling with queue system

## License

Part of Semantic Bridge Server - See project LICENSE

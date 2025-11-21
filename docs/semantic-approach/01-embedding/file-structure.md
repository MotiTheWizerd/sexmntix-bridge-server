# Embedding Module File Structure

## Directory Tree

```
src/modules/embeddings/
├── __init__.py
│
├── service/                          # Service Layer
│   ├── __init__.py
│   ├── embedding_service.py          # Main orchestrator
│   ├── config.py                     # Service configuration
│   │
│   └── components/                   # Micro-components
│       ├── validation.py             # Text validation
│       ├── cache_handler.py          # Cache operations
│       ├── event_emitter.py          # Event publishing
│       ├── response_builder.py       # Response construction
│       └── batch_processor.py        # Batch coordination
│
├── providers/                        # Provider Layer
│   ├── __init__.py
│   ├── base.py                       # Abstract base class
│   │
│   └── google/                       # Google implementation
│       ├── __init__.py
│       ├── provider.py               # Main provider class
│       ├── client.py                 # HTTP client
│       ├── request_builder.py        # Request construction
│       ├── response_parser.py        # Response parsing
│       ├── retry_handler.py          # Retry logic
│       └── batch_processor.py        # Concurrent batching
│
├── caching/                          # Caching Layer
│   ├── __init__.py
│   ├── cache.py                      # Main cache orchestrator
│   ├── cache_storage.py              # Storage operations
│   ├── key_generator.py              # Cache key generation
│   ├── expiration_handler.py         # TTL management
│   ├── eviction_strategy.py          # LRU eviction
│   └── cache_metrics.py              # Hit/miss tracking
│
├── models/                           # Data Models
│   ├── __init__.py
│   ├── config.py                     # Provider config models
│   ├── requests.py                   # Request models
│   └── responses.py                  # Response models
│
└── exceptions/                       # Exceptions
    ├── __init__.py
    └── exceptions.py                 # Custom exceptions
```

## File Responsibilities

### Service Layer

#### `service/embedding_service.py`
**Main orchestrator** for embedding generation
- Public API: `generate_embedding()`, `generate_batch()`
- Coordinates validation → cache → provider → events
- Handles errors and metrics

#### `service/config.py`
Service-level configuration
- Provider selection
- Cache settings
- Batch processing settings

#### `service/components/`
Micro-components following single responsibility:

| File | Purpose |
|------|---------|
| `validation.py` | Validates text (non-empty, encoding, length limits) |
| `cache_handler.py` | Cache get/set operations, delegates to caching layer |
| `event_emitter.py` | Publishes events (generated, cache_hit, error) |
| `response_builder.py` | Constructs `EmbeddingResponse` objects |
| `batch_processor.py` | Coordinates batch processing workflow |

### Provider Layer

#### `providers/base.py`
Abstract base class defining provider interface
```python
class EmbeddingProvider(ABC):
    @abstractmethod
    def generate_embedding(self, text: str) -> List[float]:
        pass

    @abstractmethod
    def generate_batch(self, texts: List[str]) -> List[List[float]]:
        pass

    @abstractmethod
    def health_check(self) -> ProviderHealthResponse:
        pass
```

#### `providers/google/`
Google text-embedding-004 implementation

| File | Purpose |
|------|---------|
| `provider.py` | Implements `EmbeddingProvider` for Google |
| `client.py` | HTTP client for Google API (with connection pooling) |
| `request_builder.py` | Constructs API request payloads |
| `response_parser.py` | Parses API responses, extracts embeddings |
| `retry_handler.py` | Exponential backoff retry logic |
| `batch_processor.py` | Concurrent processing (10 concurrent requests) |

### Caching Layer

#### `caching/cache.py`
Main cache orchestrator
- Public API: `get()`, `set()`, `stats()`, `clear()`
- Delegates to specialized components

#### Specialized Cache Components

| File | Purpose |
|------|---------|
| `cache_storage.py` | Low-level dict operations with thread safety |
| `key_generator.py` | Generates cache keys: `SHA256(text + model)` |
| `expiration_handler.py` | TTL-based expiration (default: 24h) |
| `eviction_strategy.py` | LRU eviction when cache is full |
| `cache_metrics.py` | Tracks hits, misses, hit rate |

### Models

#### `models/config.py`
Provider configuration models
```python
@dataclass
class ProviderConfig:
    provider_type: str  # "google", "openai", etc.
    api_key: str
    model: str
    dimensions: int
    max_retries: int
    timeout: float
```

#### `models/requests.py`
Request models
```python
@dataclass
class EmbeddingRequest:
    text: str
    model: str
    task_type: Optional[str]  # Google-specific

@dataclass
class BatchEmbeddingRequest:
    texts: List[str]
    model: str
```

#### `models/responses.py`
Response models
```python
@dataclass
class EmbeddingResponse:
    embedding: List[float]
    dimensions: int
    cached: bool
    model: str
    provider: str

@dataclass
class EmbeddingBatchResponse:
    embeddings: List[EmbeddingResponse]
    cache_hits: int
    total_count: int
    processing_time_seconds: float

@dataclass
class ProviderHealthResponse:
    healthy: bool
    provider: str
    latency_ms: float
    error: Optional[str]
```

### Exceptions

#### `exceptions/exceptions.py`
Custom exception hierarchy
```python
class EmbeddingError(Exception):
    """Base exception for embedding errors"""

class ValidationError(EmbeddingError):
    """Invalid input text"""

class ProviderError(EmbeddingError):
    """Provider API error"""

class CacheError(EmbeddingError):
    """Cache operation error"""
```

## Component Dependencies

```
EmbeddingService
    ├── TextValidator
    ├── CacheHandler
    │   └── EmbeddingCache
    │       ├── CacheStorage
    │       ├── KeyGenerator
    │       ├── ExpirationHandler
    │       ├── EvictionStrategy
    │       └── CacheMetrics
    ├── EmbeddingProvider (interface)
    │   └── GoogleEmbeddingProvider
    │       ├── GoogleClient
    │       ├── RequestBuilder
    │       ├── ResponseParser
    │       ├── RetryHandler
    │       └── BatchProcessor
    ├── EventEmitter
    └── ResponseBuilder
```

## Module Entry Points

### Primary Entry Point
```python
from src.modules.embeddings import EmbeddingService

# Initialize service
service = EmbeddingService(provider_config)

# Generate single embedding
response = service.generate_embedding("some text")

# Generate batch
batch_response = service.generate_batch(["text1", "text2"])
```

### Alternative: Direct Provider Access
```python
from src.modules.embeddings.providers.google import GoogleEmbeddingProvider

# Direct provider usage (bypasses cache)
provider = GoogleEmbeddingProvider(api_key="...")
embedding = provider.generate_embedding("some text")
```

### Cache Management
```python
from src.modules.embeddings.caching import EmbeddingCache

# Access cache directly
cache = service.cache
stats = cache.stats()
cache.clear()
```

## Design Patterns

### 1. Layered Architecture
- **Service Layer**: Business logic and coordination
- **Provider Layer**: External API integration
- **Caching Layer**: Performance optimization

### 2. Strategy Pattern
Multiple provider implementations behind common interface

### 3. Decorator Pattern
Caching wraps provider calls transparently

### 4. Observer Pattern
Event emitter publishes events to interested observers

### 5. Repository Pattern
Cache storage abstracts underlying data structure

## Navigation

- **Understand workflows**: [Single Flow](./flow-single.md) | [Batch Flow](./flow-batch.md)
- **Deep dive**: [Caching](./caching.md) | [Providers](./providers.md)
- **Component details**: [Components Reference](./components.md)

---

*Part of the [Embedding Documentation](./README.md)*

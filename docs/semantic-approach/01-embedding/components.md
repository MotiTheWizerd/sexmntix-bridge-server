# Key Components Reference

## Component Overview

| Component | Layer | Responsibility |
|-----------|-------|----------------|
| **EmbeddingService** | Service | Main orchestrator, public API |
| **TextValidator** | Service | Input validation |
| **CacheHandler** | Service | Cache coordination |
| **EventEmitter** | Service | Event publishing |
| **ResponseBuilder** | Service | Response construction |
| **BatchProcessor** | Service | Batch coordination |
| **EmbeddingProvider** | Provider | Abstract interface |
| **GoogleEmbeddingProvider** | Provider | Google implementation |
| **EmbeddingCache** | Caching | Cache orchestrator |
| **CacheStorage** | Caching | Storage operations |
| **KeyGenerator** | Caching | Cache key generation |
| **EvictionStrategy** | Caching | LRU eviction |

## Service Layer Components

### EmbeddingService

**Purpose**: Main orchestrator for embedding generation

**Public API**:
```python
class EmbeddingService:
    def generate_embedding(
        self,
        text: str
    ) -> EmbeddingResponse:
        """Generate single embedding"""

    def generate_batch(
        self,
        texts: List[str]
    ) -> EmbeddingBatchResponse:
        """Generate multiple embeddings"""

    def health_check(self) -> ProviderHealthResponse:
        """Check provider health"""

    def get_cache_stats(self) -> CacheStats:
        """Get cache statistics"""

    def clear_cache(self):
        """Clear embedding cache"""
```

**Workflow**:
1. Validate input
2. Check cache
3. Call provider if cache miss
4. Store in cache
5. Emit events
6. Return response

---

### TextValidator

**Purpose**: Validate text before processing

**Validations**:
```python
class TextValidator:
    def validate(self, text: str) -> bool:
        # Check not empty
        if not text or not text.strip():
            raise ValidationError("Text cannot be empty")

        # Check encoding
        try:
            text.encode('utf-8')
        except UnicodeEncodeError:
            raise ValidationError("Invalid UTF-8")

        # Check length
        if len(text) > MAX_LENGTH:
            raise ValidationError("Text too long")

        # Check for null bytes
        if '\x00' in text:
            raise ValidationError("Null bytes found")

        return True
```

---

### CacheHandler

**Purpose**: Coordinate cache operations

**Methods**:
```python
class CacheHandler:
    def get(
        self,
        text: str,
        model: str
    ) -> Optional[List[float]]:
        """Get embedding from cache"""
        key = self.key_gen.generate(text, model)
        return self.cache.get(key)

    def set(
        self,
        text: str,
        model: str,
        embedding: List[float]
    ):
        """Store embedding in cache"""
        key = self.key_gen.generate(text, model)
        self.cache.set(key, embedding)
```

---

### EventEmitter

**Purpose**: Publish events for monitoring

**Events**:
```python
class EventEmitter:
    def emit_generated(
        self,
        text_length: int,
        cached: bool,
        latency_ms: float
    ):
        """Emit embedding.generated event"""

    def emit_cache_hit(self, cache_key: str):
        """Emit embedding.cache_hit event"""

    def emit_error(self, error: Exception):
        """Emit embedding.error event"""

    def emit_batch_completed(self, stats: BatchStats):
        """Emit embedding.batch_generated event"""
```

---

### ResponseBuilder

**Purpose**: Construct response objects

**Methods**:
```python
class ResponseBuilder:
    def build_single(
        self,
        embedding: List[float],
        cached: bool,
        model: str,
        provider: str
    ) -> EmbeddingResponse:
        return EmbeddingResponse(
            embedding=embedding,
            dimensions=len(embedding),
            cached=cached,
            model=model,
            provider=provider
        )

    def build_batch(
        self,
        embeddings: List[EmbeddingResponse],
        processing_time: float
    ) -> EmbeddingBatchResponse:
        cache_hits = sum(1 for e in embeddings if e.cached)

        return EmbeddingBatchResponse(
            embeddings=embeddings,
            cache_hits=cache_hits,
            total_count=len(embeddings),
            processing_time_seconds=processing_time
        )
```

---

### BatchProcessor

**Purpose**: Coordinate concurrent batch processing

**Methods**:
```python
class BatchProcessor:
    def process_batch(
        self,
        texts: List[str],
        max_concurrent: int = 10
    ) -> List[EmbeddingResponse]:
        # 1. Partition cached vs uncached
        cached, uncached = self._partition(texts)

        # 2. Process uncached concurrently
        with ThreadPoolExecutor(max_workers=max_concurrent) as executor:
            futures = [
                executor.submit(self._process_single, text)
                for text in uncached
            ]
            results = [f.result() for f in futures]

        # 3. Merge cached and generated
        return self._merge_results(cached, results)
```

## Provider Layer Components

### EmbeddingProvider (Interface)

**Purpose**: Define provider contract

**Interface**:
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

---

### GoogleEmbeddingProvider

**Purpose**: Implement Google text-embedding-004

**Key Methods**:
```python
class GoogleEmbeddingProvider(EmbeddingProvider):
    def generate_embedding(self, text: str) -> List[float]:
        # Build request
        payload = self.request_builder.build(text)

        # Make API call with retry
        response = self.retry_handler.execute(
            lambda: self.client.post(payload)
        )

        # Parse response
        return self.response_parser.extract_embedding(response)
```

**Sub-components**:
- `GoogleClient`: HTTP client
- `RequestBuilder`: Payload construction
- `ResponseParser`: Response parsing
- `RetryHandler`: Retry logic

## Caching Layer Components

### EmbeddingCache

**Purpose**: Cache orchestrator

**Public API**:
```python
class EmbeddingCache:
    def get(self, key: str) -> Optional[List[float]]:
        """Get from cache"""

    def set(self, key: str, embedding: List[float]):
        """Store in cache"""

    def stats(self) -> CacheStats:
        """Get cache statistics"""

    def clear(self):
        """Clear all entries"""
```

---

### CacheStorage

**Purpose**: Thread-safe storage operations

**Methods**:
```python
class CacheStorage:
    def __init__(self):
        self._storage: Dict[str, CacheEntry] = {}
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

    def size(self) -> int:
        with self._lock:
            return len(self._storage)
```

---

### KeyGenerator

**Purpose**: Generate cache keys

**Method**:
```python
class KeyGenerator:
    def generate(self, text: str, model: str) -> str:
        data = f"{text}|{model}"
        hash_full = hashlib.sha256(data.encode()).hexdigest()
        return hash_full[:16]
```

---

### EvictionStrategy

**Purpose**: Implement LRU eviction

**Method**:
```python
class EvictionStrategy:
    def find_eviction_candidate(
        self,
        storage: Dict[str, CacheEntry]
    ) -> str:
        """Find least recently used entry"""
        lru_key = None
        lru_time = None

        for key, entry in storage.items():
            if lru_time is None or entry.last_accessed < lru_time:
                lru_time = entry.last_accessed
                lru_key = key

        return lru_key
```

## Component Interactions

```
User Request
     ↓
EmbeddingService
     ↓
TextValidator → validates
     ↓
CacheHandler → checks cache
     ├─ HIT → return
     └─ MISS ↓
GoogleEmbeddingProvider
     ├─ RequestBuilder
     ├─ GoogleClient
     ├─ RetryHandler
     └─ ResponseParser
          ↓
CacheHandler → stores
     ↓
ResponseBuilder → formats
     ↓
EventEmitter → publishes
     ↓
Return to User
```

## Testing Components

### Unit Testing

```python
def test_text_validator():
    validator = TextValidator()

    # Valid text
    assert validator.validate("Hello world") == True

    # Empty text
    with pytest.raises(ValidationError):
        validator.validate("")

    # Null bytes
    with pytest.raises(ValidationError):
        validator.validate("Hello\x00world")
```

### Integration Testing

```python
def test_embedding_service_with_cache():
    service = EmbeddingService(provider=mock_provider)

    # First call - cache miss
    response1 = service.generate_embedding("test")
    assert response1.cached == False

    # Second call - cache hit
    response2 = service.generate_embedding("test")
    assert response2.cached == True
    assert response1.embedding == response2.embedding
```

## Performance Characteristics

| Component | Time Complexity | Notes |
|-----------|----------------|-------|
| **TextValidator** | O(n) | n = text length |
| **KeyGenerator** | O(n) | SHA256 hash |
| **CacheStorage.get** | O(1) | Dict lookup |
| **CacheStorage.set** | O(k) | k = cache size (LRU scan) |
| **GoogleProvider** | O(1) | Network latency |
| **BatchProcessor** | O(n/m) | n = texts, m = concurrency |

---

*Part of the [Embedding Documentation](./README.md)*

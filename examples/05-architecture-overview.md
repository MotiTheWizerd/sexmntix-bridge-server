# Architecture Overview

## System Layers

Semantix-Brain follows **Clean Architecture** principles with clear separation of concerns.

```
┌─────────────────────────────────────────────────┐
│              API Layer (FastAPI)                │
│  HTTP Endpoints → User-facing interface         │
└─────────────────────┬───────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│          Service Layer (Business Logic)         │
│  Orchestration, validation, event publishing    │
└─────────────────────┬───────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│     Repository Layer (Data Access)              │
│  CRUD operations, search, recency boost         │
└─────────────────────┬───────────────────────────┘
                      ↓
┌─────────────────────────────────────────────────┐
│     Infrastructure Layer (External Services)    │
│  ChromaDB, Google Embeddings, Config, Logging   │
└─────────────────────────────────────────────────┘
```

---

## Directory Structure

```
semantix-brain/
├── src/
│   ├── main.py                    # FastAPI application entry
│   ├── core/                      # Core system components
│   │   ├── plugin_manager.py     # Module discovery & DI
│   │   └── services/              # Shared services
│   │       └── embedding_service.py
│   ├── infrastructure/            # External integrations
│   │   ├── chromadb/
│   │   │   └── client.py          # ChromaDB wrapper
│   │   ├── embeddings/
│   │   │   └── embedding_service.py  # Google API client
│   │   ├── config/
│   │   │   └── settings.py        # Environment config
│   │   └── logging/
│   │       └── logger.py          # Logging setup
│   ├── modules/                   # Business modules
│   │   ├── memory/                # Memory system
│   │   │   ├── domain/
│   │   │   │   └── models.py      # Domain entities
│   │   │   ├── repository.py      # Data access
│   │   │   ├── service.py         # Business logic
│   │   │   └── api.py             # HTTP endpoints
│   │   ├── notebook/              # Notebook system
│   │   └── mcp/                   # MCP protocol module
│   ├── events/
│   │   └── event_bus.py           # Event-driven architecture
│   └── shared/                    # Shared utilities
├── scripts/
│   └── migrate.py                 # Migration tools
├── data/
│   └── chromadb/                  # Vector database storage
└── tests/                         # Test suites
```

---

## Layer Responsibilities

### 1. API Layer

**Files:** `src/modules/memory/api.py`, `src/main.py`

**Responsibilities:**
- HTTP endpoint definitions
- Request validation (Pydantic models)
- Response formatting
- Error handling
- CORS configuration

**Example:**
```python
@router.post("/search")
async def search_memories(request: SearchRequest):
    results = await memory_service.search(
        query=request.query,
        limit=request.limit
    )
    return {"results": results}
```

### 2. Service Layer

**File:** `src/modules/memory/service.py`

**Responsibilities:**
- Orchestrate business operations
- Coordinate repository + embedding service
- Apply business rules
- Publish domain events
- Handle complex workflows

**Example:**
```python
class MemoryService:
    async def add_memory(self, memory_data: MemoryCreate) -> Memory:
        # 1. Create domain object
        memory = Memory(**memory_data)

        # 2. Generate embedding
        text = memory.to_embedding_text()
        embedding = await self.embedding_service.generate_embedding(text)

        # 3. Store
        saved = await self.repository.add(memory, embedding)

        # 4. Publish event
        await self.event_bus.publish(MemoryCreatedEvent(saved))

        return saved
```

### 3. Repository Layer

**File:** `src/modules/memory/repository.py`

**Responsibilities:**
- Direct data access (ChromaDB operations)
- Query construction
- Result transformation
- Similarity calculations
- Recency boosting
- Collection management

**Example:**
```python
class MemoryRepository:
    async def search(
        self,
        query_embedding: list[float],
        limit: int = 10,
        where_filter: dict | None = None
    ) -> list[SearchResult]:
        collection = await self._get_collection()

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where=where_filter
        )

        search_results = self._to_search_results(results)
        boosted = self._apply_recency_boost(search_results)

        return boosted
```

### 4. Infrastructure Layer

**Files:** `src/infrastructure/*`

**Responsibilities:**
- External service integration
- Configuration management
- Logging setup
- Database connections
- API clients

**Components:**

#### ChromaDB Client
```python
class ChromaDBClient:
    def __init__(self, path: str):
        self.client = chromadb.PersistentClient(path=path)

    def get_collection(self, name: str):
        return self.client.get_or_create_collection(name)
```

#### Embedding Service
```python
class EmbeddingService:
    async def generate_embedding(self, text: str) -> list[float]:
        response = await self.http_client.post(
            self.api_url,
            json={"model": "text-embedding-004", ...}
        )
        return response.json()["embedding"]["values"]
```

#### Settings
```python
class Settings(BaseSettings):
    google_api_key: str
    chromadb_path: str = "./data/chromadb"
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
```

---

## Domain Models

**File:** `src/modules/memory/domain/models.py`

### Core Entities

#### Memory
```python
class Memory(BaseModel):
    task: str
    component: str
    agent: str
    date: str
    summary: str
    root_cause: str | None
    solution: str | None
    tags: list[str]
    temporal_context: TemporalContext
    file_name: str | None
    lesson: str | None
```

#### SearchResult
```python
class SearchResult(BaseModel):
    memory: Memory
    similarity: float  # 0.0 to 1.0
    distance: float    # L2 distance
```

#### TemporalContext
```python
class TemporalContext(BaseModel):
    date: str              # "2025-11-12"
    time_period: str       # "recent", "last-week", etc.
    quarter: str           # "Q4 2025"
    year: str              # "2025"
    days_since_epoch: int  # For calculations
```

---

## Dependency Injection

**File:** `src/core/plugin_manager.py`

### Plugin Architecture

Each module is a self-contained plugin:

```python
class MemoryModule:
    def __init__(self, settings: Settings, event_bus: EventBus):
        # Infrastructure
        chromadb_client = ChromaDBClient(settings.chromadb_path)
        embedding_service = EmbeddingService(settings.google_api_key)

        # Repository
        self.repository = MemoryRepository(chromadb_client)

        # Service
        self.service = MemoryService(
            repository=self.repository,
            embedding_service=embedding_service,
            event_bus=event_bus
        )

    def get_router(self) -> APIRouter:
        return create_memory_router(self.service)
```

### Auto-Discovery

```python
# Plugin manager discovers all modules
plugin_manager = PluginManager()
plugin_manager.discover_modules("src/modules")

# Registers routes automatically
for module in plugin_manager.modules:
    app.include_router(module.get_router())
```

---

## Event-Driven Architecture

**File:** `src/events/event_bus.py`

### Event Types

```python
class MemoryCreatedEvent:
    memory: Memory
    timestamp: datetime

class MemorySearchedEvent:
    query: str
    result_count: int
    timestamp: datetime
```

### Publishing Events

```python
# Service layer
await event_bus.publish(MemoryCreatedEvent(memory))
```

### Subscribing to Events

```python
# Other modules can listen
@event_bus.subscribe(MemoryCreatedEvent)
async def on_memory_created(event: MemoryCreatedEvent):
    logger.info(f"New memory: {event.memory.task}")
```

---

## Data Flow: Complete Request

### Example: Search Request

```
1. HTTP Request
   POST /memory/search
   {"query": "permission issues", "limit": 5}
        ↓

2. API Layer (api.py)
   - Validate request
   - Call service.search()
        ↓

3. Service Layer (service.py)
   - Generate query embedding via EmbeddingService
   - Call repository.search()
        ↓

4. Repository Layer (repository.py)
   - Query ChromaDB collection
   - Calculate similarity scores
   - Apply recency boost
   - Return SearchResult[]
        ↓

5. Service Layer
   - Publish MemorySearchedEvent
   - Return results to API
        ↓

6. API Layer
   - Format response
   - Return JSON
        ↓

7. HTTP Response
   {
     "results": [
       {"memory": {...}, "similarity": 0.884},
       ...
     ]
   }
```

---

## Key Design Patterns

### 1. Repository Pattern
- Abstracts data access
- Enables easy testing (mock repository)
- Could swap ChromaDB for another DB

### 2. Service Layer Pattern
- Business logic separated from data access
- Orchestrates multiple operations
- Publishes domain events

### 3. Dependency Injection
- Services receive dependencies via constructor
- Loose coupling between layers
- Easy to test and modify

### 4. Plugin Architecture
- Modules are self-contained
- Easy to add/remove features
- Inter-module communication via events

### 5. Clean Architecture
- Dependencies point inward
- Domain models don't know about infrastructure
- Business logic independent of frameworks

---

## Key Files for Replication

If you're building this in Python:

### 1. Embedding Service
```python
# src/infrastructure/embeddings/embedding_service.py
import httpx

class EmbeddingService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.url = "https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent"
        self.client = httpx.AsyncClient(timeout=30.0)

    async def generate_embedding(self, text: str) -> list[float]:
        response = await self.client.post(
            self.url,
            json={
                "model": "models/text-embedding-004",
                "content": {"parts": [{"text": text}]}
            },
            headers={"x-goog-api-key": self.api_key}
        )
        return response.json()["embedding"]["values"]
```

### 2. ChromaDB Client
```python
# src/infrastructure/chromadb/client.py
import chromadb

class ChromaDBClient:
    def __init__(self, path: str = "./data/chromadb"):
        self.client = chromadb.PersistentClient(path=path)
        self._collections = {}

    def get_collection(self, name: str):
        if name not in self._collections:
            self._collections[name] = self.client.get_or_create_collection(name)
        return self._collections[name]
```

### 3. Repository
```python
# src/modules/memory/repository.py
class MemoryRepository:
    def __init__(self, chromadb_client: ChromaDBClient):
        self.client = chromadb_client

    async def add(self, memory: Memory, embedding: list[float]) -> Memory:
        collection = self.client.get_collection("memories")

        collection.add(
            ids=[memory.task],
            embeddings=[embedding],
            documents=[memory.model_dump_json()],
            metadatas=[self._to_metadata(memory)]
        )

        collection.count()  # Force index rebuild
        return memory

    async def search(
        self,
        query_embedding: list[float],
        limit: int = 10
    ) -> list[SearchResult]:
        collection = self.client.get_collection("memories")

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=limit
        )

        return self._to_search_results(results)
```

### 4. Service
```python
# src/modules/memory/service.py
class MemoryService:
    def __init__(
        self,
        repository: MemoryRepository,
        embedding_service: EmbeddingService
    ):
        self.repository = repository
        self.embedding_service = embedding_service

    async def add_memory(self, memory: Memory) -> Memory:
        text = memory.to_embedding_text()
        embedding = await self.embedding_service.generate_embedding(text)
        return await self.repository.add(memory, embedding)

    async def search(self, query: str, limit: int = 10) -> list[SearchResult]:
        embedding = await self.embedding_service.generate_embedding(query)
        return await self.repository.search(embedding, limit)
```

---

## Dependencies (pyproject.toml)

```toml
[project]
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn>=0.27.0",
    "chromadb>=0.4.22",
    "pydantic>=2.5.0",
    "httpx>=0.26.0",
]
```

---

## Minimal Working Example

Here's everything you need in ~50 lines:

```python
import chromadb
import httpx
from pydantic import BaseModel

# 1. Domain Model
class Memory(BaseModel):
    task: str
    content: str

# 2. Embedding Service
async def generate_embedding(text: str, api_key: str) -> list[float]:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent",
            json={"model": "models/text-embedding-004", "content": {"parts": [{"text": text}]}},
            headers={"x-goog-api-key": api_key}
        )
        return response.json()["embedding"]["values"]

# 3. Storage
chroma_client = chromadb.PersistentClient(path="./data/chromadb")
collection = chroma_client.get_or_create_collection("memories")

# 4. Add Memory
async def add_memory(memory: Memory, api_key: str):
    embedding = await generate_embedding(memory.content, api_key)
    collection.add(
        ids=[memory.task],
        embeddings=[embedding],
        documents=[memory.model_dump_json()]
    )
    collection.count()  # Force index rebuild

# 5. Search
async def search(query: str, api_key: str, limit: int = 5):
    embedding = await generate_embedding(query, api_key)
    results = collection.query(query_embeddings=[embedding], n_results=limit)
    return results["documents"]

# Usage
await add_memory(Memory(task="fix-bug", content="Fixed race condition in streaming"), api_key)
results = await search("streaming bugs", api_key)
```

That's the entire system in its simplest form!

---

## Summary

The architecture is designed for:
- ✅ **Modularity** - Easy to add/remove features
- ✅ **Testability** - Clear separation enables mocking
- ✅ **Scalability** - Plugin system supports growth
- ✅ **Maintainability** - Clean layers, single responsibility
- ✅ **Reusability** - Infrastructure services shared across modules

You can replicate this design in any Python project by following the layered approach and using the minimal dependencies (FastAPI, ChromaDB, httpx, Pydantic).

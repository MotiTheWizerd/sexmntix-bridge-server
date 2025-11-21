# Integration Layer

## Overview

The system exposes three integration points: REST API, MCP Tools, and Direct SDK access.

## REST API Endpoints

### Embeddings

```
POST /embeddings
Generate single embedding

POST /embeddings/batch
Generate multiple embeddings

GET /embeddings/health
Check provider health

GET /embeddings/cache/stats
Get cache statistics

DELETE /embeddings/cache
Clear cache
```

### Memory Logs

```
POST /memory-logs
Create new memory (triggers embedding & storage)

GET /memory-logs
List memories

GET /memory-logs/{id}
Get specific memory

DELETE /memory-logs/{id}
Delete memory
```

### Search

```
POST /search
Semantic search for similar memories
```

## MCP Server Tools

### semantic_search
```python
{
    "query": "authentication bug",
    "user_id": "user123",
    "project_id": "project456",
    "limit": 10,
    "min_similarity": 0.7
}
```

### generate_embedding
```python
{
    "text": "some text",
    "user_id": "user123",
    "project_id": "project456"
}
```

### store_memory
```python
{
    "user_id": "user123",
    "project_id": "project456",
    "memory_log": {
        "task": "Fix bug",
        "summary": "...",
        ...
    }
}
```

## Event Bus

### Published Events

- `memory_log.stored` - New memory created
- `embedding.generated` - Embedding created
- `embedding.cache_hit` - Cache hit occurred
- `vector.stored` - Vector stored in ChromaDB
- `search.completed` - Search completed

### Subscribing to Events

```python
@event_bus.subscribe("memory_log.stored")
async def handle_memory_stored(payload):
    memory_id = payload["memory_log_id"]
    # Process...
```

## Key Files

```
src/api/routes/
├── embeddings.py         # Embedding endpoints
├── memory_logs.py        # Memory CRUD endpoints
└── search.py             # Search endpoint

src/modules/xcp_server/tools/
├── semantic_search/      # MCP search tool
├── embedding/            # MCP embedding tool
└── store_memory/         # MCP store tool

src/events/
├── internal_handlers/    # Event handlers
└── event_bus.py          # Event bus implementation
```

---

*Part of the [Semantic Approach Documentation](../README.md)*

# Semantic Search Architecture Overview

## What is Semantic Search?

Semantic search allows you to find information based on **meaning** rather than exact keyword matches. When you search for "authentication bug fix", the system understands the concepts and finds related memories about login issues, security patches, or credential problems—even if they use different words.

## Core Concept: Embeddings

**Embeddings** are numerical representations of text that capture semantic meaning:
- Text → Vector (list of 768 numbers)
- Similar meanings → Similar vectors
- "login error" and "authentication failure" have vectors close together
- "database query" has a vector far from authentication topics

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     SEMANTIC SEARCH SYSTEM                   │
│                                                              │
│  [User Query] → [Embedding] → [Vector Search] → [Results]  │
│                                                              │
│  ┌────────────────┐  ┌──────────────┐  ┌────────────────┐ │
│  │   EMBEDDING    │  │   STORAGE    │  │     SEARCH     │ │
│  │   Generation   │  │   Dual DB    │  │   Pipeline     │ │
│  │                │  │              │  │                │ │
│  │  • Google API  │  │ • PostgreSQL │  │ • 5 Stages     │ │
│  │  • Caching     │  │ • ChromaDB   │  │ • Filtering    │ │
│  │  • Validation  │  │ • Events     │  │ • Ranking      │ │
│  └────────────────┘  └──────────────┘  └────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Key Design Principles

### 1. Dual Storage Architecture
- **PostgreSQL**: Persistent data, relational queries, embeddings backup
- **ChromaDB**: Optimized vector search, HNSW indexing, fast retrieval

Why both? PostgreSQL provides reliability and structure; ChromaDB provides speed for vector operations.

### 2. Event-Driven Storage
Memory storage is non-blocking:
1. Save memory to PostgreSQL (fast, synchronous)
2. Emit event
3. Background handler generates embedding and stores in ChromaDB
4. No waiting for embedding generation during API calls

### 3. Pluggable Provider Architecture
Embedding generation is provider-agnostic:
- Currently: Google text-embedding-004
- Easy to add: OpenAI, Cohere, Voyage, custom models
- Interface: `EmbeddingProvider` base class

### 4. Multi-Tenancy by Design
Complete isolation per user/project:
- **PostgreSQL**: Filtered by `user_id` + `project_id` columns
- **ChromaDB**: Separate collections per tenant (hash-based naming)
- No data leakage between users

### 5. Performance Optimization
- **LRU Cache**: In-memory cache (1000 items, 24h TTL)
- **Batch Processing**: Concurrent embedding generation (10 concurrent)
- **Lazy Storage**: Non-blocking vector storage via events
- **Connection Pooling**: Single shared ChromaDB instance

## Data Flow at a Glance

### Write Path (Storing Memories)
```
User → API → PostgreSQL → Event
                            ↓
              Handler → Extract Text → Generate Embedding
                                              ↓
                                    ChromaDB + PostgreSQL Update
```

### Read Path (Searching)
```
Query → Embed Query → ChromaDB Search → Filter → Rank → Results
```

## Component Layers

### Layer 1: Embedding Generation
- Provider abstraction
- Google API integration
- LRU caching
- Validation and error handling

→ See [01-embedding/](../01-embedding/README.md)

### Layer 2: Vector Storage
- Text extraction from structured data
- Dual database coordination
- Event-driven workflow
- Multi-tenant isolation

→ See [02-storage/](../02-storage/README.md)

### Layer 3: Semantic Search
- 5-stage search pipeline
- Similarity filtering
- Temporal decay ranking
- Rich metadata queries

→ See [03-search/](../03-search/README.md)

### Layer 4: Integration
- REST API endpoints
- MCP server tools
- Event bus architecture

→ See [04-integration/](../04-integration/README.md)

## Key Technologies

| Technology | Purpose | Why This Choice |
|------------|---------|-----------------|
| **Google text-embedding-004** | Embedding generation | 768 dimensions, high quality, cost-effective |
| **ChromaDB** | Vector search | Open source, HNSW indexing, Python-native |
| **PostgreSQL + pgvector** | Persistent storage | Relational data + vector support in one DB |
| **Event Bus** | Async coordination | Non-blocking, decoupled components |
| **LRU Cache** | Performance | Fast repeated lookups, automatic eviction |

## Performance Characteristics

### Embedding Generation
- **Cold (API call)**: ~200-500ms per embedding
- **Hot (cached)**: <1ms per embedding
- **Batch processing**: 10 concurrent requests

### Vector Search
- **ChromaDB query**: ~10-50ms for 10 results
- **Total search time**: ~100-300ms (including embedding generation)
- **Scales to**: Millions of vectors per collection

### Storage
- **PostgreSQL write**: ~5-10ms
- **ChromaDB write**: ~10-20ms
- **Event handling**: Async, non-blocking

## Common Use Cases

1. **Finding Similar Memories**
   - "Show me all authentication bug fixes"
   - Searches by semantic meaning, not keywords

2. **Time-Aware Search**
   - Recent memories ranked higher
   - Exponential decay based on age

3. **Filtered Search**
   - By component: "frontend authentication bugs"
   - By date range: "memories from last month"
   - By tags: "critical bugs"

4. **Cross-Project Learning**
   - Search across all user's projects
   - Or isolate to specific project

## Next Steps

- **New to embeddings?** Start with [architecture-diagram.md](./architecture-diagram.md) for visual overview
- **Want implementation details?** Jump to specific sections:
  - [Embedding Generation](../01-embedding/README.md)
  - [Storage Mechanism](../02-storage/README.md)
  - [Search Pipeline](../03-search/README.md)
- **Looking for specific info?** Check [05-reference/](../05-reference/README.md)

---

*Part of the [Semantic Approach Documentation](../README.md)*

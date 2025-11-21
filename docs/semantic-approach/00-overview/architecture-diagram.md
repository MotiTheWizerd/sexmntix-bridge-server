# Architecture Diagram

## Complete System Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           CLIENT LAYER                                      │
│                                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐                │
│  │  REST API    │    │  MCP Tools   │    │  Direct SDK  │                │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘                │
│         │                   │                   │                          │
└─────────┼───────────────────┼───────────────────┼──────────────────────────┘
          │                   │                   │
┌─────────┼───────────────────┼───────────────────┼──────────────────────────┐
│         │       SERVICE LAYER (Business Logic)  │                          │
│         ↓                   ↓                   ↓                          │
│  ┌────────────────────────────────────────────────────────┐               │
│  │           EMBEDDING SERVICE                            │               │
│  │  ┌─────────┐  ┌─────────┐  ┌──────────────┐          │               │
│  │  │Validator│  │  Cache  │  │EventEmitter  │          │               │
│  │  └─────────┘  └─────────┘  └──────────────┘          │               │
│  │         ↓                                              │               │
│  │  ┌─────────────────────────────────┐                  │               │
│  │  │   Provider (Google/OpenAI/etc)  │                  │               │
│  │  └─────────────────────────────────┘                  │               │
│  └────────────────────────────────────────────────────────┘               │
│                          ↓                                                 │
│  ┌────────────────────────────────────────────────────────┐               │
│  │           STORAGE ORCHESTRATION                        │               │
│  │  ┌──────────────┐  ┌──────────────────────────┐       │               │
│  │  │Text Extractor│  │MemoryStorageHandler      │       │               │
│  │  └──────────────┘  └──────────────────────────┘       │               │
│  └────────────────────────────────────────────────────────┘               │
│                          ↓                                                 │
│  ┌────────────────────────────────────────────────────────┐               │
│  │           SEARCH ORCHESTRATION                         │               │
│  │  ┌──────────────────────────────────────────────┐     │               │
│  │  │ SearchWorkflowOrchestrator (5 stages)        │     │               │
│  │  │  1. Embedding  2. Search  3. Filter          │     │               │
│  │  │  4. Rank       5. Response                   │     │               │
│  │  └──────────────────────────────────────────────┘     │               │
│  └────────────────────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────────────────────┘
                          ↓                    ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                      STORAGE LAYER                                          │
│                                                                             │
│  ┌─────────────────────────────┐    ┌─────────────────────────────┐       │
│  │      POSTGRESQL              │    │       CHROMADB              │       │
│  │  ┌────────────────────────┐  │    │  ┌────────────────────────┐│       │
│  │  │   memory_logs          │  │    │  │  Collections (HNSW)    ││       │
│  │  │  • id                  │  │    │  │  • memory_logs_{hash}  ││       │
│  │  │  • user_id             │  │    │  │  • mental_notes_{hash} ││       │
│  │  │  • project_id          │  │    │  │                        ││       │
│  │  │  • raw_data (JSONB)    │  │    │  │  Per collection:       ││       │
│  │  │  • embedding (vector)  │  │    │  │  • id                  ││       │
│  │  │  • created_at          │  │    │  │  • embedding [768]     ││       │
│  │  │  • ...metadata         │  │    │  │  • document (JSON)     ││       │
│  │  └────────────────────────┘  │    │  │  • metadata (dict)     ││       │
│  │                               │    │  └────────────────────────┘│       │
│  │  Indexes:                     │    │                             │       │
│  │  • user_id, project_id        │    │  Index: HNSW               │       │
│  │  • embedding (pgvector)       │    │  Metric: L2 (Euclidean)    │       │
│  └─────────────────────────────┘    └─────────────────────────────┘       │
│                                                                             │
│  Purpose: Persistent storage,        Purpose: Fast vector search,          │
│           relational queries,                 HNSW indexing                │
│           backup embeddings                                                │
└─────────────────────────────────────────────────────────────────────────────┘
                          ↑                    ↑
┌─────────────────────────────────────────────────────────────────────────────┐
│                      EVENT BUS                                              │
│                                                                             │
│  memory_log.stored → MemoryLogStorageHandler → [Extract → Embed → Store]  │
│  embedding.generated → Metrics & Logging                                   │
│  vector.stored → Completion notifications                                  │
│  search.completed → Telemetry                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Write Flow (Store Memory)

```
┌──────────┐
│  Client  │
└─────┬────┘
      │ POST /memory-logs
      ↓
┌─────────────────────┐
│  API Route Handler  │
└─────────┬───────────┘
          │
          ↓ [Synchronous]
┌────────────────────────┐
│  PostgreSQL            │
│  INSERT memory_log     │
│  (without embedding)   │
└────────┬───────────────┘
         │
         ↓ Emit "memory_log.stored"
┌─────────────────────────────────────┐
│     EVENT BUS                       │
└────────┬────────────────────────────┘
         │ [Asynchronous]
         ↓
┌──────────────────────────────────────┐
│  MemoryLogStorageHandler             │
│                                      │
│  1. Extract searchable text          │
│     ↓                                │
│  2. Generate embedding               │
│     ├─→ Check cache                  │
│     └─→ Call Google API (if miss)   │
│     ↓                                │
│  3. Store in ChromaDB                │
│     ├─→ Collection: memory_logs_{h} │
│     ├─→ ID: memory_log_123          │
│     ├─→ Embedding: [float] * 768    │
│     └─→ Document: {raw_data}        │
│     ↓                                │
│  4. Update PostgreSQL                │
│     └─→ SET embedding = [...]       │
└──────────────────────────────────────┘
         │
         ↓ Emit "vector.stored"
┌──────────────────────┐
│   Complete           │
└──────────────────────┘
```

## Read Flow (Search)

```
┌──────────┐
│  Client  │
└─────┬────┘
      │ POST /search
      │ {"query": "auth bug"}
      ↓
┌─────────────────────────────────────┐
│  SearchWorkflowOrchestrator         │
└─────────────────────────────────────┘
      │
      ↓ Stage 1: Embedding
┌────────────────────────────┐
│  EmbeddingService          │
│  • Check cache             │
│  • Generate if miss        │
│  • Return vector [768]     │
└────────┬───────────────────┘
         │
         ↓ Stage 2: Vector Search
┌────────────────────────────┐
│  ChromaDB                  │
│  collection.query()        │
│  • query_embeddings        │
│  • n_results = limit       │
│  • Returns: matches with   │
│    distances               │
└────────┬───────────────────┘
         │
         ↓ Stage 3: Filter
┌────────────────────────────┐
│  SimilarityFilter          │
│  • Convert L2 → similarity │
│  • Filter by min_threshold │
└────────┬───────────────────┘
         │
         ↓ Stage 4: Rank
┌────────────────────────────┐
│  TemporalDecayRanker       │
│  • Apply time decay        │
│  • Rerank by weighted      │
│    similarity              │
└────────┬───────────────────┘
         │
         ↓ Stage 5: Response
┌────────────────────────────┐
│  ResponseBuilder           │
│  • Format results          │
│  • Add metadata            │
│  • Calculate metrics       │
└────────┬───────────────────┘
         │
         ↓
┌──────────────────────┐
│  Return to Client    │
│  {results, count,    │
│   duration, metrics} │
└──────────────────────┘
```

## Multi-Tenancy Architecture

```
User: "user123", Project: "project456"
                  │
                  ↓
         ┌────────────────┐
         │ Hash Function  │
         │ SHA256(user:   │
         │ project)[:16]  │
         └────────┬───────┘
                  │
                  ↓
         hash = "a1b2c3d4e5f6g7h8"
                  │
    ┌─────────────┼─────────────┐
    │             │             │
    ↓             ↓             ↓
┌─────────┐  ┌─────────────┐  ┌─────────────┐
│PostgreSQL│  │  ChromaDB   │  │  ChromaDB   │
│         │  │ Collection  │  │ Collection  │
│ WHERE   │  │             │  │             │
│ user_id │  │memory_logs_ │  │mental_notes_│
│  = '123'│  │a1b2c3d4...  │  │a1b2c3d4...  │
│ AND     │  │             │  │             │
│project_id│ └─────────────┘  └─────────────┘
│  = '456'│
└─────────┘

Result: Complete data isolation per tenant
```

## Component Dependency Graph

```
┌─────────────────────────────────────────────────┐
│  External Dependencies                          │
│  • Google Generative AI API                     │
│  • ChromaDB Server                              │
│  • PostgreSQL with pgvector                     │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────┼────────────────────────────────┐
│  Infrastructure Layer                           │
│                ↓                                │
│  ┌──────────────────┐   ┌──────────────────┐   │
│  │ ChromaDB Client  │   │ PostgreSQL ORM   │   │
│  └──────────────────┘   └──────────────────┘   │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────┼────────────────────────────────┐
│  Core Services │                                │
│                ↓                                │
│  ┌──────────────────────────────────────┐      │
│  │     EmbeddingService                 │      │
│  │  (Uses: Provider, Cache, Validator)  │      │
│  └──────────────────────────────────────┘      │
│                ↓                                │
│  ┌──────────────────────────────────────┐      │
│  │     VectorRepository                 │      │
│  │  (Uses: ChromaDB, Collections)       │      │
│  └──────────────────────────────────────┘      │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────┼────────────────────────────────┐
│  Orchestration │                                │
│                ↓                                │
│  ┌──────────────────────────────────────┐      │
│  │  MemoryStorageHandler                │      │
│  │  (Uses: EmbeddingService,            │      │
│  │          VectorRepository,           │      │
│  │          TextExtractor)              │      │
│  └──────────────────────────────────────┘      │
│                                                 │
│  ┌──────────────────────────────────────┐      │
│  │  SearchWorkflowOrchestrator          │      │
│  │  (Uses: EmbeddingService,            │      │
│  │          VectorRepository,           │      │
│  │          Filters, Rankers)           │      │
│  └──────────────────────────────────────┘      │
└────────────────┬────────────────────────────────┘
                 │
┌────────────────┼────────────────────────────────┐
│  API Layer     ↓                                │
│  ┌────────────────┐   ┌────────────────┐       │
│  │  REST Routes   │   │   MCP Tools    │       │
│  └────────────────┘   └────────────────┘       │
└─────────────────────────────────────────────────┘
```

## Data Model Relationships

```
┌──────────────────────────────────────────┐
│  PostgreSQL: memory_logs                 │
│                                          │
│  id: 123                                 │
│  user_id: "user123"                      │
│  project_id: "project456"                │
│  raw_data: {...}                         │
│  embedding: [0.1, 0.2, ..., 0.8] (768)  │
│  created_at: 2025-01-15                  │
└──────────────┬───────────────────────────┘
               │
               │ Mirrored in ↓
               │
┌──────────────┴───────────────────────────┐
│  ChromaDB: memory_logs_a1b2c3d4e5f6g7h8  │
│                                          │
│  id: "memory_log_123"                    │
│  embedding: [0.1, 0.2, ..., 0.8] (768)  │
│  document: "{...raw_data...}"            │
│  metadata: {                             │
│    date: "2025-01-15",                   │
│    task: "Fix auth bug",                 │
│    component: "auth-service",            │
│    tags: ["bug", "security"]             │
│  }                                       │
└──────────────────────────────────────────┘

Why both?
- PostgreSQL: Source of truth, relational queries
- ChromaDB: Fast vector search, HNSW indexing
```

---

*Part of the [Overview Documentation](./README.md)*

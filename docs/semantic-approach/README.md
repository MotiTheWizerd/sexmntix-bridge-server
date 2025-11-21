# Semantic Search Architecture Documentation

Complete documentation for the embedding/vectorization system that powers semantic memory search.

## 📚 Documentation Structure

### [00-overview/](./00-overview/)
**Start here!** High-level architecture and design principles.

- [Overview](./00-overview/README.md) - System introduction and key concepts
- [Architecture Diagram](./00-overview/architecture-diagram.md) - Visual system architecture

### [01-embedding/](./01-embedding/)
**How text becomes vectors.** Embedding generation with Google text-embedding-004.

- [Overview](./01-embedding/README.md) - Embedding module introduction
- [File Structure](./01-embedding/file-structure.md) - Module organization
- [Single Flow](./01-embedding/flow-single.md) - Single embedding generation
- [Batch Flow](./01-embedding/flow-batch.md) - Batch processing
- [Caching](./01-embedding/caching.md) - LRU cache mechanism
- [Providers](./01-embedding/providers.md) - Provider architecture
- [Components](./01-embedding/components.md) - Key components reference

### [02-storage/](./02-storage/)
**Dual database architecture.** PostgreSQL + ChromaDB for persistent and fast vector storage.

- [Overview](./02-storage/README.md) - Storage module introduction
- [Dual Storage](./02-storage/dual-storage.md) - Why two databases
- [ChromaDB](./02-storage/chromadb.md) - Vector database details
- [PostgreSQL](./02-storage/postgresql.md) - Schema and pgvector
- [Multi-Tenancy](./02-storage/multi-tenancy.md) - Isolation strategy
- [Event-Driven Flow](./02-storage/event-driven-flow.md) - Async storage
- [Text Extraction](./02-storage/text-extraction.md) - Memory to text

### [03-search/](./03-search/)
**5-stage search pipeline.** From query to ranked results.

- [Overview](./03-search/README.md) - Search pipeline introduction

### [04-integration/](./04-integration/)
**API, MCP, and Events.** How to use the system.

- [Overview](./04-integration/README.md) - Integration points

### [05-reference/](./05-reference/)
**Quick reference.** Component index, file index, glossary.

- [Overview](./05-reference/README.md) - Reference documentation

## 🎯 Quick Navigation

### By Role

**I'm a backend developer**
→ Start with [00-overview](./00-overview/) → [02-storage](./02-storage/) → [04-integration](./04-integration/)

**I'm working on search**
→ Start with [00-overview](./00-overview/) → [03-search](./03-search/) → [01-embedding](./01-embedding/)

**I'm new to embeddings**
→ Start with [00-overview](./00-overview/) → [01-embedding/flow-single](./01-embedding/flow-single.md)

**I need to add a feature**
→ Start with [00-overview/architecture-diagram](./00-overview/architecture-diagram.md) → Find relevant section

### By Task

**"How do I search for similar memories?"**
→ [03-search/README.md](./03-search/README.md)

**"How are embeddings generated?"**
→ [01-embedding/flow-single.md](./01-embedding/flow-single.md)

**"How is data stored?"**
→ [02-storage/dual-storage.md](./02-storage/dual-storage.md)

**"How does multi-tenancy work?"**
→ [02-storage/multi-tenancy.md](./02-storage/multi-tenancy.md)

**"How do I add a new embedding provider?"**
→ [01-embedding/providers.md](./01-embedding/providers.md)

**"What's the caching strategy?"**
→ [01-embedding/caching.md](./01-embedding/caching.md)

**"How do events work?"**
→ [02-storage/event-driven-flow.md](./02-storage/event-driven-flow.md)

## 🔑 Key Concepts

### Embedding
Numerical representation of text as a 768-dimensional vector. Similar meanings → similar vectors.

### Semantic Search
Find information by meaning, not keywords. "auth bug" finds "login error", "credential issue", etc.

### Dual Storage
PostgreSQL (persistent) + ChromaDB (fast vector search) working together.

### Multi-Tenancy
Complete data isolation per user+project using collection-based separation.

### Event-Driven
Non-blocking storage: API responds fast, embedding/storage happens in background.

### HNSW
Hierarchical Navigable Small World - fast approximate nearest neighbor search.

## 📊 System Stats

| Metric | Value |
|--------|-------|
| **Embedding Model** | Google text-embedding-004 |
| **Dimensions** | 768 |
| **Cache Hit Rate** | 70-90% (typical) |
| **Search Latency** | 100-300ms |
| **Storage Latency** | 10-20ms (user sees) |
| **Vector Index** | HNSW (ChromaDB) |
| **Distance Metric** | L2 (Euclidean) |

## 🚀 Getting Started

1. **Read [Overview](./00-overview/README.md)** - Understand the system
2. **Study [Architecture Diagram](./00-overview/architecture-diagram.md)** - See how it fits together
3. **Deep dive into relevant section** - Based on your task
4. **Use [Reference](./05-reference/README.md)** - For quick lookups

## 🔧 Tech Stack

- **Embedding**: Google Generative AI API
- **Vector DB**: ChromaDB with HNSW indexing
- **Primary DB**: PostgreSQL with pgvector
- **Language**: Python 3.10+
- **API**: FastAPI
- **MCP**: Model Context Protocol

## 📝 Documentation Goals

- **Conceptual**: Understand the "why" behind decisions
- **Practical**: Learn "how" to use and extend the system
- **Reference**: Quick lookup for specific information
- **Visual**: Diagrams and examples throughout

## 💡 Contributing

When updating the system:

1. Update relevant documentation
2. Add examples if introducing new concepts
3. Update diagrams if architecture changes
4. Keep docs in sync with code

---

**Last Updated**: 2025-01-21

**Maintained By**: Semantix Development Team

**Feedback**: Report issues or suggest improvements

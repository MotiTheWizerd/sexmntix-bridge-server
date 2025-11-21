# Reference Documentation

## Component Index

### Embedding Layer
- **EmbeddingService** - Main orchestrator
- **GoogleEmbeddingProvider** - Google API integration
- **EmbeddingCache** - LRU cache (1000 items, 24h TTL)
- **TextValidator** - Input validation
- **BatchProcessor** - Concurrent batch processing

### Storage Layer
- **MemoryStorageHandler** - Storage orchestration
- **MemoryTextExtractor** - Text extraction from memories
- **VectorRepository** - ChromaDB operations
- **ChromaDBClient** - Database client
- **CollectionManager** - Multi-tenant collections

### Search Layer
- **SearchWorkflowOrchestrator** - 5-stage pipeline
- **BaseSearchHandler** - Public search API
- **EmbeddingStage** - Query embedding
- **SearchStage** - Vector search
- **ProcessingStage** - Filtering & ranking
- **ResponseStage** - Response formatting

### Integration Layer
- **API Routes** - REST endpoints
- **MCP Tools** - Claude desktop integration
- **Event Handlers** - Async processing

## File Index

See [file-index.md](./file-index.md) for complete file listing.

## Glossary

**Embedding**: Numerical vector representation of text (768 dimensions)

**Vector**: List of numbers representing semantic meaning

**Similarity**: How close two embeddings are (0-1 scale)

**HNSW**: Hierarchical Navigable Small World graph index

**L2 Distance**: Euclidean distance between vectors

**LRU Cache**: Least Recently Used eviction strategy

**Temporal Decay**: Time-based ranking boost for recent items

**Multi-tenancy**: Data isolation per user/project

**Collection**: ChromaDB container for vectors

**pgvector**: PostgreSQL extension for vector operations

---

*Part of the [Semantic Approach Documentation](../README.md)*

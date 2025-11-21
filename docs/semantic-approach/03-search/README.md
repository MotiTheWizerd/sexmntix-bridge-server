# Semantic Search Pipeline

## Overview

The search module implements a 5-stage pipeline for finding similar memories based on semantic meaning.

## 5-Stage Pipeline

```
Query → [1] Embed → [2] Search → [3] Filter → [4] Rank → [5] Response
```

### Stage 1: Embedding Generation
- Convert query text to 768-dimensional vector
- Use cache if available
- Same embedding service as storage

### Stage 2: Vector Search
- Query ChromaDB with embedding
- HNSW index finds nearest neighbors
- Returns matches with distances

### Stage 3: Filtering
- Convert L2 distance to similarity score
- Apply minimum similarity threshold
- Remove results below threshold

### Stage 4: Ranking
- Optional temporal decay (boost recent memories)
- Re-rank by weighted similarity
- Sort by final score

### Stage 5: Response Building
- Format results for API
- Add metadata (count, duration, cache status)
- Return to user

## Search Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | Required | Search text |
| `user_id` | string | Required | User isolation |
| `project_id` | string | Required | Project isolation |
| `limit` | int | 10 | Max results |
| `min_similarity` | float | 0.0 | Threshold (0-1) |
| `enable_temporal_decay` | bool | false | Boost recent |
| `half_life_days` | int | 30 | Decay rate |

## Example Usage

```python
results = search_handler.search_similar_memories(
    query="authentication bug fixes",
    user_id="user123",
    project_id="project456",
    limit=10,
    min_similarity=0.7,
    enable_temporal_decay=True
)
```

## Performance

| Metric | Typical Value |
|--------|---------------|
| **Total latency** | 100-300ms |
| **Embedding** | 50-250ms (or <1ms cached) |
| **Vector search** | 10-50ms |
| **Filtering/ranking** | 5-10ms |

## Key Files

```
src/modules/vector_storage/search/
├── handler/
│   ├── base_handler.py                    # Public API
│   └── orchestrator/
│       ├── orchestrator.py                # Pipeline coordinator
│       └── stages/
│           ├── embedding_stage.py         # Stage 1
│           ├── search_stage.py            # Stage 2
│           ├── processing_stage.py        # Stage 3 & 4
│           └── response_stage.py          # Stage 5
│
└── filters/
    ├── similarity_filters.py              # Min similarity
    └── temporal_decay.py                  # Time-based ranking
```

---

*Part of the [Semantic Approach Documentation](../README.md)*

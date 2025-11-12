# Text-to-Vector Flow

## Complete Journey: From Memory Input to Vector Storage

This document explains how raw memory data becomes a searchable vector embedding.

---

## Step 1: Memory Creation

**File:** `semantix-brain/src/modules/memory/service.py`
**Method:** `MemoryService.add_memory()`

### Input: Memory Data
```python
{
    "task": "permission-dialog-redesign",
    "component": "ui-permission-system",
    "date": "2025-11-12",
    "summary": "Complete redesign with compact dark metallic theme",
    "root_cause": "Outdated heavy glassmorphism...",
    "solution": "Complete redesign with modern dark theme...",
    "tags": ["permission-dialog", "ui-redesign", "glassmorphism"],
    "lesson": "Keep UI consistent across components"
}
```

### Process
1. Create `Memory` domain object from input
2. Validate all required fields
3. Pass to embedding generation

---

## Step 2: Text Preparation for Embedding

**File:** `semantix-brain/src/modules/memory/domain/models.py`
**Method:** `Memory.to_embedding_text()`

### Purpose
Combine all relevant memory fields into a single searchable text string.

### What Gets Combined

```python
def to_embedding_text(self) -> str:
    parts = []

    # Temporal context
    if self.temporal_context:
        parts.append(f"Date: {self.temporal_context.date}")
        parts.append(f"Period: {self.temporal_context.time_period}")
        parts.append(f"Quarter: {self.temporal_context.quarter}")

    # Core fields
    parts.append(f"Component: {self.component}")
    parts.append(f"Agent: {self.agent}")
    parts.append(f"Task: {self.task}")
    parts.append(f"Summary: {self.summary}")

    # Tags
    if self.tags:
        parts.append(f"Tags: {', '.join(self.tags)}")

    # Detailed content
    if self.root_cause:
        parts.append(f"Root Cause: {self.root_cause}")
    if self.solution:
        parts.append(f"Solution: {self.solution}")
    if self.lesson:
        parts.append(f"Lesson: {self.lesson}")

    return "\n\n".join(parts)
```

### Example Output
```
Date: 2025-11-12
Period: recent
Quarter: Q4 2025

Component: ui-permission-system
Agent: claude
Task: permission-dialog-redesign
Summary: Complete redesign with compact dark metallic theme

Tags: permission-dialog, ui-redesign, glassmorphism

Root Cause: Outdated heavy glassmorphism design with inconsistent styling

Solution: Complete redesign with modern dark metallic theme matching system messages

Lesson: Keep UI consistent across components for better UX
```

---

## Step 3: Generate Embedding Vector

**File:** `semantix-brain/src/infrastructure/embeddings/embedding_service.py`
**Method:** `EmbeddingService.generate_embedding(text: str)`

### Input
The combined text string from Step 2

### API Call
```python
response = await client.post(
    "https://generativelanguage.googleapis.com/v1beta/models/text-embedding-004:embedContent",
    json={
        "model": "models/text-embedding-004",
        "content": {"parts": [{"text": text}]}
    },
    headers={"x-goog-api-key": api_key}
)
```

### Output: Vector Embedding
```python
[
    0.0234, -0.1234, 0.5678, -0.0123, 0.8901, ...
    # Typically 768 dimensions for text-embedding-004
]
```

This vector mathematically represents the **semantic meaning** of the memory.

---

## Step 4: Storage Preparation

**File:** `semantix-brain/src/modules/memory/repository.py`
**Method:** `MemoryRepository.add()`

### Data Preparation for ChromaDB

```python
# 1. Generate unique ID
memory_id = memory.file_name or f"{memory.task}_{memory.date}"

# 2. Prepare metadata (flat dict for filtering)
metadata = {
    "task": memory.task,
    "agent": memory.agent,
    "component": memory.component,
    "date": memory.date,
    "tags": ",".join(memory.tags),
    # Temporal context fields
    "time_period": memory.temporal_context.time_period,
    "quarter": memory.temporal_context.quarter,
    "year": memory.temporal_context.year
}

# 3. Full memory as JSON document
document = memory.model_dump_json()
```

---

## Step 5: Vector Storage in ChromaDB

### Storage Call
```python
collection.add(
    ids=[memory_id],
    embeddings=[embedding_vector],
    documents=[document],
    metadatas=[metadata]
)
```

### Force Index Rebuild
```python
# Trigger HNSW index update for immediate searchability
collection.count()
```

---

## Complete Flow Diagram

```
User Input (JSON)
       ↓
Memory Object Created
       ↓
to_embedding_text()
       ↓
Combined Text String
       ↓
EmbeddingService.generate_embedding()
       ↓
HTTP POST → Google API
       ↓
Vector (list[float])
       ↓
Prepare: ID + Metadata + Document
       ↓
ChromaDB.collection.add()
       ↓
Vector Stored + Indexed
       ↓
✅ Available for Semantic Search
```

---

## Key Files Reference

| Step | File | Responsibility |
|------|------|----------------|
| 1 | `src/modules/memory/service.py` | Orchestrate memory creation |
| 2 | `src/modules/memory/domain/models.py` | Convert memory to text |
| 3 | `src/infrastructure/embeddings/embedding_service.py` | Generate vector via Google API |
| 4-5 | `src/modules/memory/repository.py` | Store in ChromaDB |

---

## Important Notes

### Why Combine All Fields?
- Makes memories searchable by ANY field
- No need to know exact field names when searching
- Natural language queries work across all content

### Why Not Embed Individual Fields?
- Would require multiple vectors per memory
- Higher API costs
- More complex retrieval logic
- Single vector is sufficient for semantic search

### Embedding Caching
- Once created, embeddings are stored in ChromaDB
- Never re-generated unless memory text changes
- Saves API costs and processing time

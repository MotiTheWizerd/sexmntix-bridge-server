# Conversation ChromaDB Pipeline Documentation

## Overview
Conversations are stored in **TWO separate systems**:
1. **PostgreSQL** - Structured data storage
2. **ChromaDB** - Vector embeddings in **separate collection**

---

## Complete Pipeline Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. CLIENT REQUEST                                                │
│    POST /conversations                                           │
│    {                                                             │
│      "conversation_id": "uuid",                                  │
│      "model": "gpt-5-1-instant",                                 │
│      "conversation": [                                           │
│        {"role": "user", "text": "..."},                          │
│        {"role": "assistant", "text": "..."}                      │
│      ]                                                           │
│    }                                                             │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. FASTAPI ROUTE (conversations.py:27)                          │
│    @router.post("")                                              │
│    - Validates request data                                      │
│    - Checks for duplicate conversation_id                        │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. POSTGRESQL STORAGE (synchronous)                             │
│    ConversationRepository.create()                               │
│    - Stores in "conversations" table                             │
│    - NO embedding column (no pgvector dependency!)               │
│    - Returns conversation.id immediately                         │
│                                                                  │
│    Table: conversations                                          │
│    Columns: id, conversation_id, model, raw_data,                │
│             user_id, project_id, created_at                      │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 4. EVENT EMISSION (conversations.py:107)                        │
│    event_bus.publish("conversation.stored", event_data)          │
│    - Triggers background processing                              │
│    - Non-blocking (doesn't wait for completion)                  │
│    - Returns response to client immediately                      │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. EVENT HANDLER (background task)                              │
│    ConversationStorageHandler.handle_conversation_stored()       │
│    Location: src/events/internal_handlers/handlers/              │
│              conversation_handler.py                             │
│                                                                  │
│    Steps:                                                        │
│    a) Extract and validate event data (line 40)                  │
│    b) Call orchestrator.store_conversation_vector() (line 103)   │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. ORCHESTRATOR (orchestrators.py:114)                          │
│    VectorStorageOrchestrator.store_conversation_vector()         │
│    - Creates VectorStorageService for user/project               │
│    - Delegates to service layer                                  │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. VECTOR STORAGE SERVICE (service.py:349)                      │
│    VectorStorageService.store_conversation_vector()              │
│                                                                  │
│    Steps:                                                        │
│    a) Extract messages from conversation array (line 378)        │
│    b) Combine all message texts (line 384):                      │
│       "user: How do I... assistant: You can..."                  │
│    c) Generate embedding via EmbeddingService (line 398)         │
│    d) Call create_conversation() CRUD operation (line 412)       │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. CHROMADB CRUD OPERATION                                      │
│    create_conversation() in operations/conversation/crud.py      │
│                                                                  │
│    Steps:                                                        │
│    a) Get SEPARATE collection (line 75):                         │
│       client.get_conversation_collection(user_id, project_id)    │
│       ⚠️  Uses conversations_{hash} NOT semantix_{hash}          │
│                                                                  │
│    b) Generate unique ID (line 78):                              │
│       "conversation_{db_id}_{user_id}_{project_id}"              │
│                                                                  │
│    c) Prepare metadata (line 81):                                │
│       - conversation_id (UUID)                                   │
│       - model                                                    │
│       - message_count                                            │
│       - user_id, project_id                                      │
│                                                                  │
│    d) Build document (line 89):                                  │
│       JSON.dumps(conversation_data)                              │
│                                                                  │
│    e) Add to ChromaDB (line 92):                                 │
│       collection.add(                                            │
│         ids=[conversation_id],                                   │
│         embeddings=[embedding],                                  │
│         documents=[document],                                    │
│         metadatas=[metadata]                                     │
│       )                                                          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Key Components

### 1. ChromaDB Client (`client.py:105`)
```python
def get_conversation_collection(user_id: str, project_id: str) -> Collection:
    """
    Get or create SEPARATE collection for conversations.

    Collection name: conversations_{hash16}
    NOT: semantix_{hash16}

    This isolates conversations from memory_logs and mental_notes.
    """
```

### 2. Collection Naming Strategy
- **Memory Logs & Mental Notes**: `semantix_{hash16}`
- **Conversations**: `conversations_{hash16}` ✅ SEPARATE!

Hash is computed from: `SHA256(user_id:project_id)`

Example:
- User: "test_user_1", Project: "test_project"
- Hash: "a1b2c3d4e5f6g7h8"
- Memory collection: `semantix_a1b2c3d4e5f6g7h8`
- Conversation collection: `conversations_a1b2c3d4e5f6g7h8`

### 3. Text Extraction Strategy
Conversations combine ALL messages into a single text:

```python
combined_text = " ".join([
    f"{msg['role']}: {msg['text']}"
    for msg in messages
])
```

Example:
```
Input:
[
  {"role": "user", "text": "How do I auth?"},
  {"role": "assistant", "text": "Use JWT tokens"}
]

Output for embedding:
"user: How do I auth? assistant: Use JWT tokens"
```

---

## Storage Comparison

### PostgreSQL (conversations table)
```
Column           | Type        | Description
-----------------|-------------|----------------------------------
id               | INTEGER     | Primary key
conversation_id  | VARCHAR     | UUID from client
model            | VARCHAR     | AI model name
raw_data         | JSONB       | Full conversation data
user_id          | VARCHAR     | User identifier
project_id       | VARCHAR     | Project identifier
created_at       | TIMESTAMP   | Creation timestamp
```

**NO embedding column!** ❌ No pgvector dependency!

### ChromaDB (conversations_{hash} collection)
```
Field      | Type          | Description
-----------|---------------|----------------------------------
id         | STRING        | conversation_{db_id}_{user}_{project}
embedding  | VECTOR(768)   | Embedding from combined messages
document   | STRING        | JSON.dumps(conversation_data)
metadata   | DICT          | Flat metadata for filtering
```

Metadata includes:
- `conversation_id` - UUID
- `model` - AI model name
- `message_count` - Number of messages
- `user_id`, `project_id` - Identifiers
- `created_at` - Timestamp

---

## Search Flow

### Semantic Search (`POST /conversations/search`)

```
┌─────────────────────────────────────────────────────────────────┐
│ CLIENT REQUEST                                                   │
│ POST /conversations/search                                       │
│ {                                                                │
│   "query": "authentication with JWT",                            │
│   "user_id": "test_user_1",                                      │
│   "project_id": "test_project",                                  │
│   "limit": 5                                                     │
│ }                                                                │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. Generate query embedding                                      │
│    EmbeddingService.generate_embedding("authentication...")      │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. Query ChromaDB SEPARATE collection                           │
│    collection = conversations_{hash}  ← NOT semantix_{hash}      │
│    collection.query(                                             │
│      query_embeddings=[query_embedding],                         │
│      n_results=5,                                                │
│      where={"model": "gpt-5-1-instant"}  # optional filter       │
│    )                                                             │
└────────────────────┬────────────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. Return results with similarity scores                         │
│    [                                                             │
│      {                                                           │
│        "conversation_id": "uuid",                                │
│        "similarity": 0.87,                                       │
│        "document": "{...}",                                      │
│        "metadata": {"model": "...", "message_count": 2}          │
│      }                                                           │
│    ]                                                             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Verification Checklist

✅ **Event Handler Registered**
- File: `src/api/dependencies/event_handlers.py:87`
- Event: `"conversation.stored"`
- Handler: `conversation_handlers.handle_conversation_stored`

✅ **ChromaDB Collection Method Exists**
- File: `src/infrastructure/chromadb/client.py:105`
- Method: `get_conversation_collection(user_id, project_id)`
- Returns: Separate collection with `conversations_` prefix

✅ **CRUD Operations Exist**
- File: `src/infrastructure/chromadb/operations/conversation/crud.py`
- Functions: `create_conversation`, `read_conversation`, `delete_conversation`

✅ **VectorStorageService Method Exists**
- File: `src/modules/vector_storage/service.py:349`
- Method: `store_conversation_vector()`
- Returns: `(conversation_id, embedding)`

✅ **Search Method Exists**
- File: `src/modules/vector_storage/service.py:428`
- Method: `search_similar_conversations()`
- Searches: `conversations_{hash}` collection

---

## Testing the Pipeline

Run the test script:
```bash
# Start the server
poetry run python main.py

# In another terminal, run the test
poetry run python test_conversation_pipeline.py
```

Expected output:
```
[1] Creating conversation in PostgreSQL...
✅ Conversation created with ID: 123

[2] Waiting for background vector storage (3 seconds)...

[3] Verifying conversation in PostgreSQL...
✅ Found in PostgreSQL

[4] Searching in ChromaDB conversations collection...
✅ Search completed. Found 1 results
   ✅ FOUND OUR CONVERSATION IN CHROMADB!
```

---

## Common Issues

### 1. Conversation not found in search
**Cause**: Background handler hasn't completed yet
**Solution**: Wait 2-3 seconds after creation before searching

### 2. Search returns empty results
**Possible causes**:
- Event handler not registered (check startup logs)
- ChromaDB collection not created
- Embedding generation failed

**Debug**:
```bash
# Check server logs for:
[CONVERSATION_HANDLER] Calling store_conversation_vector
[CONVERSATION_STORAGE] Generating embedding...
[CONVERSATION_STORAGE] Stored in ChromaDB collection conversations_{hash}
[CONVERSATION_CRUD] Added conversation to collection
```

### 3. Wrong collection being searched
**Cause**: Using `semantix_{hash}` instead of `conversations_{hash}`
**Solution**: Verify `client.get_conversation_collection()` is called

---

## Summary

🎯 **Two Storage Systems**:
- PostgreSQL: Structured data (no embeddings!)
- ChromaDB: Vectors in **separate** `conversations_{hash}` collection

🎯 **Event-Driven**:
- PostgreSQL storage is synchronous (immediate response)
- ChromaDB storage is asynchronous (background task)

🎯 **Complete Isolation**:
- Memory logs: `semantix_{hash}` collection
- Mental notes: `semantix_{hash}` collection
- Conversations: `conversations_{hash}` collection ✅

🎯 **No pgvector Dependency**:
- PostgreSQL has NO embedding column
- All vectors stored exclusively in ChromaDB

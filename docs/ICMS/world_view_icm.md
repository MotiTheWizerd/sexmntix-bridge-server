# World View ICM (Internal Context Memory)

The World View ICM constructs a high-level summary of the user's recent history and context. It bridges the gap between immediate short-term memory and long-term retrieval.

## Purpose

*   **Context Aggregation**: Collects recent conversations and interactions.
*   **Summarization**: Optionally uses an LLM to generate a concise summary ("short-term memory") of recent events.
*   **Caching**: Can cache the computed world view to reduce latency and cost on subsequent requests within the same session.

## Implementation

*   **Wrapper**: `src/services/conversation_memory_pipeline/world_view.py`
*   **Service**: `src/services/world_view_service.py`
*   **Class**: `WorldViewService`

## Input

*   `user_id`: User ID.
*   `project_id`: Project ID.
*   `session_id`: Optional Session ID.
*   `summarize_with_llm`: Boolean flag to enable LLM-based summarization.

## Output Schema

```json
{
    "user_id": "string",
    "project_id": "string",
    "session_id": "string",
    "conversation_count": int,
    "is_first_conversation": bool,
    "recent_conversations": [
        {
            "id": "uuid",
            "conversation_id": "uuid",
            "session_id": "string",
            "model": "string",
            "created_at": "ISO8601 string",
            "snippet": "string",       // First 200 chars of first message
            "summary": "string",       // Constructed summary of first/last messages
            "first_text": "string",    // Full text of first message
            "last_text": "string"      // Full text of last message
        }
    ],
    "recent_memory_logs": [],          // Currently empty placeholder
    "recent_mental_notes": [],         // Currently empty placeholder
    "short_term_memory": "string",     // LLM-generated summary (if enabled)
    "is_cached": bool,                 // Whether this result came from cache
    "generated_at": "ISO8601 string"
}
```

## Logic

1.  **Cache Check**: The pipeline wrapper first checks if a valid world view exists in the `icm_logs` table for the current session. If so, it returns the cached version.
2.  **Data Gathering**:
    *   Queries the database for the most recent conversations (default limit: 5) for the user/project.
    *   Counts total conversations.
3.  **Processing**:
    *   Extracts text from conversation JSON structures.
    *   Strips internal memory blocks (`[semantix-memory-block]`) to avoid polluting the context.
4.  **Summarization (Optional)**:
    *   If `summarize_with_llm` is true, constructs a prompt with the recent conversation summaries.
    *   Calls the LLM service (worker type `world_view_summarizer`) to generate a cohesive paragraph.
    *   Alternatively, can use a `CompressionBrain` if configured (though LLM service is preferred).
5.  **Result Construction**: Assembles the payload.

## Caching Mechanism

The `ConversationMemoryPipeline` handles the caching logic. When a new world view is computed (i.e., not loaded from cache), the pipeline logs it to the database via `log_world_view_icm`. Subsequent requests can then retrieve this log entry.

# Session ICM (Internal Context Memory)

The Session ICM provides basic statistics and state information about the current user session. It is a lightweight component designed to give immediate context about the "freshness" of the interaction.

## Purpose

*   **Session Tracking**: Identifies the current session.
*   **Interaction Counting**: Counts how many conversations have occurred in this session.
*   **New User Detection**: Determines if this is the first conversation in the session.

## Implementation

*   **File**: `src/services/conversation_memory_pipeline/session_state.py`
*   **Function**: `compute_session_state`

## Input

*   `session_id`: The ID of the current session.
*   `user_id`: User ID.
*   `project_id`: Project ID.
*   `db_manager`: Database manager instance.

## Output Schema

```json
{
    "session_id": "string",
    "conversation_count": int,      // Number of conversations in this session
    "is_first_conversation": bool   // True if count <= 1
}
```

## Logic

1.  **Validation**: Checks if `session_id` and `db_manager` are present. Returns `None` if not.
2.  **Database Query**:
    *   Uses `ConversationRepository` to count conversations matching the `session_id`, `user_id`, and `project_id`.
3.  **State Calculation**:
    *   `is_first_conversation` is derived from the count (count <= 1).
4.  **Error Handling**: Catches database exceptions, logs a warning, and returns `None`.

## Usage

This component is typically fast and low-cost. Its output helps the LLM understand if it should welcome the user back or continue an ongoing flow.

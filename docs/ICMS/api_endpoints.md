# ICMS API Endpoints

Currently, the ICMS components are primarily internal to the `ConversationMemoryPipeline`. However, some functionality is exposed via the API.

## Exposed Endpoints

### 1. World View (`/world-view`)

*   **Method**: `GET`
*   **Path**: `/world-view`
*   **Purpose**: Computes or retrieves the "World View" summary for a user/project/session.
*   **Parameters**:
    *   `user_id` (required)
    *   `project_id` (required)
    *   `session_id` (optional)
    *   `summarize_with_llm` (optional, default: true)
*   **Returns**: `WorldViewResponse` (JSON object containing recent conversations summary).

### 2. ICM Logs (`/icm-logs`)

*   **Method**: `GET`
*   **Path**: `/icm-logs`
*   **Purpose**: Lists historical execution logs of ICM components.
*   **Parameters**:
    *   `user_id`, `project_id`, `icm_type`, `request_id`, `start_time`, `end_time`
*   **Returns**: List of log entries showing inputs and outputs of past ICM runs.

### 3. Fetch Memory (`/conversations/fetch-memory`)

*   **Method**: `POST`
*   **Path**: `/conversations/fetch-memory`
*   **Purpose**: Triggers the full `ConversationMemoryPipeline`.
*   **Description**: This is the main entry point that orchestrates all ICMs (Intent, Time, Identity, Session, World View) to retrieve relevant memories.
*   **Returns**: A complex object containing the results of all ICMs and the retrieved memories.

## Internal Components (No Direct Endpoint)

The following components do not have dedicated individual API endpoints and are accessed via the pipeline:

*   **Intent ICM**: Accessed internally during `fetch-memory`.
*   **Time ICM**: Accessed internally during `fetch-memory`.
*   **Identity ICM**: Accessed internally during `fetch-memory`.
*   **Session ICM**: Accessed internally during `fetch-memory`.

## Future Work

If granular access to specific ICMs is needed (e.g., "just resolve this time string" or "just classify this intent"), new endpoints could be added to a dedicated `/icm` router.

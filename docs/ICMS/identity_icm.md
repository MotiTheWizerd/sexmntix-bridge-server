# Identity ICM (Internal Context Memory)

The Identity ICM provides a consistent identity profile for the user and the project. It ensures that the AI always has context about who it is talking to and what role it should play.

## Purpose

*   **User Context**: Provides details about the user (role, preferences, goals).
*   **Assistant Persona**: Defines the assistant's personality, style, and safety guidelines.
*   **Project Context**: Links the interaction to a specific project.

## Implementation

*   **Wrapper**: `src/services/conversation_memory_pipeline/identity.py`
*   **Service**: `src/services/identity_service.py`
*   **Class**: `IdentityICMService`

## Input

*   `user_id`: The ID of the user.
*   `project_id`: The ID of the project.

## Output Schema

The Identity ICM returns a dictionary. The structure can be dynamic based on configuration, but a default skeleton looks like this:

```json
{
    "user_id": "string",
    "project_id": "string",
    "user_identity": {
        "role": "user",
        "goals": [],
        "preferences": [],
        "constraints": [],
        "tone": "concise and clear"
    },
    "assistant_identity": {
        "role": "assistant",
        "style": "helpful, direct, precise",
        "safety": "respect privacy; avoid hallucination; ask before assuming"
    },
    "system_policies": [],
    "recent_profile_events": []
}
```

## Logic

1.  **Configuration Check**: Checks if a static `identity_json` blob was provided during initialization (e.g., from environment variables).
2.  **Parsing**: If provided, parses the JSON and injects `user_id` and `project_id`.
3.  **Fallback**: If no configuration is present, returns a hardcoded minimal skeleton with default values for user and assistant roles.
4.  **Error Handling**: If parsing fails, logs a warning and falls back to the default skeleton.

## Usage in Pipeline

The pipeline calls `compute_identity` which delegates to `IdentityICMService.get_identity`. This ensures that even if the database is down or configuration is missing, a valid identity object is always returned to the prompt construction phase.

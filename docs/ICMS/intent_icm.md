# Intent ICM (Internal Context Memory)

The Intent ICM is responsible for classifying the user's intent from their query. It uses a Small Language Model (SLM) - specifically `SXPrefrontalModel` (Qwen) - to analyze the text and determine the best course of action.

## Purpose

*   **Classification**: Identify the type of user request (e.g., factual question, personal question, action request).
*   **Routing**: Determine the appropriate retrieval strategy (e.g., semantic search, skip retrieval).
*   **Extraction**: Identify specific entities or topics that require memory retrieval.

## Implementation

*   **File**: `src/modules/SXPrefrontal/brains/icm/brain.py`
*   **Class**: `ICMBrain`

## Input

*   `text`: The user's query string.
*   `context`: Optional additional context string.

## Output Schema

The Intent ICM returns a dictionary with the following structure:

```json
{
    "intent": "string",             // e.g., "factual", "personal", "action", "unknown"
    "confidence": float,            // 0.0 to 1.0
    "confidence_reason": "string",  // Explanation for the confidence score
    "route": "string",              // e.g., "triage", "direct_answer"
    "required_memory": ["string"],  // List of topics/entities to search for
    "retrieval_strategy": "string", // e.g., "pgvector", "none"
    "entities": ["string"],         // Extracted entities
    "fallback": {
        "intent": "string",
        "route": "string"
    },
    "notes": "string"
}
```

## Logic

1.  **Prompt Construction**: Builds a system prompt defining the intent schema and a user prompt containing the query.
2.  **Generation**: Calls `SXPrefrontalModel.generate` to get a JSON response.
3.  **Parsing**: Parses the JSON output, handling potential markdown fencing.
4.  **Normalization**: Ensures all required keys are present, filling in defaults if necessary.
5.  **Error Handling**: Returns a default "unknown" intent if generation or parsing fails.

## Default Response

If the model fails to generate a valid response, the following default is returned:

```json
{
    "intent": "unknown",
    "confidence": 0.0,
    "confidence_reason": "Unable to determine intent",
    "route": "triage",
    "required_memory": [],
    "retrieval_strategy": "none",
    "entities": [],
    "fallback": {
        "intent": "unknown",
        "route": "triage"
    },
    "notes": ""
}
```

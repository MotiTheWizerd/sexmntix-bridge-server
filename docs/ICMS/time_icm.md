# Time ICM (Internal Context Memory)

The Time ICM resolves relative time expressions in the user's query into absolute UTC time windows. This is crucial for filtering memories by time (e.g., "what did I do yesterday?").

## Purpose

*   **Resolution**: Convert phrases like "yesterday", "last week", "this morning" into specific start and end timestamps.
*   **Context Awareness**: Uses the current time (`now`) and user's timezone offset to calculate accurate windows.

## Implementation

*   **File**: `src/modules/SXPrefrontal/brains/time_icm/brain.py`
*   **Class**: `TimeICMBrain`
*   **Default LLM Provider**: Mistral (`mistral-tiny`)
*   **Supported Providers**: Mistral, Qwen, Gemini (configurable via user settings)

## Input

*   `text`: The user's query string.
*   `now`: Optional `datetime` object representing "now" (defaults to UTC now).
*   `tz_offset_minutes`: Optional integer representing the user's timezone offset from UTC.

## Output Schema

The Time ICM returns a dictionary with the following structure:

```json
{
    "time_expression": "string",       // The detected time phrase (e.g., "yesterday")
    "start_time": "ISO8601 string",    // Start of the time window (UTC)
    "end_time": "ISO8601 string",      // End of the time window (UTC)
    "resolution_confidence": float,    // 0.0 to 1.0
    "granularity": "string",           // e.g., "day", "week", "hour"
    "notes": "string"                  // Debugging notes or failure reasons
}
```

## Logic

1.  **Context Setup**: Determines the current reference time (`now`) in UTC.
2.  **Prompt Construction**: Builds a prompt including the user text, current ISO time, and timezone offset.
3.  **Generation**: Calls `SXPrefrontalModel.generate` to interpret the time expression.
4.  **Parsing & Normalization**: Parses the JSON response and ensures valid fields.
5.  **Fallback**: If the LLM fails to identify a time expression, it defaults to using the original text for potential keyword matching, though `start_time` and `end_time` will be null.

## Key Methods

*   `resolve(text, now, tz_offset_minutes)`: Main entry point for resolution.
*   `_last_night_window(now, tz_offset_minutes)`: Helper (internal logic, though not directly exposed in the main `resolve` flow unless called specifically) to calculate "last night" windows.

## Configuration

The Time ICM uses **Mistral Tiny** by default for fast and cost-effective time resolution. Users can override the provider and model through their user configuration:

```json
{
  "icm_config": {
    "time_icm": {
      "provider": "mistral",
      "model": "mistral-tiny"
    }
  }
}
```

**Supported Providers:**
*   `mistral` - Mistral AI models (default: `mistral-tiny`)
*   `qwen` - Qwen models
*   `gemini` - Google Gemini models

## Default Response

If resolution fails:

```json
{
    "time_expression": "",
    "start_time": null,
    "end_time": null,
    "resolution_confidence": 0.2,
    "granularity": "unknown",
    "notes": "failed to resolve"
}
```

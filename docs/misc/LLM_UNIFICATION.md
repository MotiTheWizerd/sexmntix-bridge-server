# LLM Unification - Single Source of Truth

## Overview

Unified all LLM calls through a centralized `LLMService` to ensure consistent user-specific model configuration across the application.

## Architecture

### Before
- **3 separate LLM call locations:**
  - `SXThalamus/gemini/client.py` - Duplicate GeminiClient
  - `basic-agent/client.py` - Duplicate GeminiClient  
  - `conversations.py` - Direct GeminiClient instantiation
- **Inconsistent config:** Only SXThalamus respected user config
- **Cache duplication:** Each service had its own client cache

### After
- **Single LLM module:** `src/modules/llm/`
- **Centralized service:** `LLMService` manages all LLM operations
- **Unified caching:** One cache for all user-specific clients
- **Consistent config:** All workers use user's database configuration

## New Structure

```
src/modules/llm/
├── __init__.py          # Module exports
├── client.py            # GeminiClient (single implementation)
├── service.py           # LLMService (centralized management)
└── exceptions.py        # LLM-specific exceptions
```

## LLMService API

```python
from src.modules.llm import LLMService

# Initialize (done in bootstrap)
llm_service = LLMService(
    db_manager=db_manager,
    default_timeout=30.0
)

# Generate content with user-specific model
result = await llm_service.generate_content(
    prompt="Your prompt here",
    user_id="user-uuid",
    worker_type="conversation_analyzer"  # or "memory_synthesizer"
)

# Get client directly (if needed)
client = await llm_service.get_client(
    user_id="user-uuid",
    worker_type="conversation_analyzer"
)

# Cache management
llm_service.invalidate_cache(user_id)  # Clear user's cached clients
llm_service.clear_cache()              # Clear all cached clients
```

## Worker Types

Each worker type maps to user's `background_workers` config:

- `conversation_analyzer` - SXThalamus conversation processing
- `memory_synthesizer` - Memory synthesis in conversations route

## Integration Points

### 1. Bootstrap (app.py)
```python
# Initialize LLM service
llm_service = initialize_llm_service(app.state.db_manager, logger)
app.state.llm_service = llm_service

# Pass to SXThalamus
sxthalamus_service = initialize_sxthalamus(event_bus, logger, llm_service)
```

### 2. SXThalamus Service
```python
# Receives LLM service via DI
def __init__(self, event_bus, logger, llm_service, config):
    self.llm_service = llm_service

# Uses it for processing
result = await self.llm_service.generate_content(
    prompt=prompt,
    user_id=user_id,
    worker_type="conversation_analyzer"
)
```

### 3. Conversations Route
```python
# Access from app state
llm_service = request.app.state.llm_service

# Use for memory synthesis
synthesized_memory = await llm_service.generate_content(
    prompt=prompt,
    user_id=user_id,
    worker_type="memory_synthesizer"
)
```

## Benefits

1. **Single source of truth** - One place for all LLM calls
2. **Consistent config** - All workers respect user's model preferences
3. **Unified caching** - Efficient client reuse across workers
4. **Easy maintenance** - Update LLM logic in one place
5. **Testability** - Mock LLMService for all tests
6. **Extensibility** - Easy to add new providers (OpenAI, Anthropic)

## User Configuration

Users can configure models per worker in database:

```json
{
  "background_workers": {
    "conversation_analyzer": {
      "provider": "google",
      "model": "gemini-2.5-flash",
      "enabled": true
    },
    "memory_synthesizer": {
      "provider": "google",
      "model": "gemini-2.0-flash",
      "enabled": true
    }
  }
}
```

## Cache Behavior

- **Key format:** `{user_id}:{worker_type}`
- **Invalidation:** Call `invalidate_cache(user_id)` when user updates config
- **Restart:** Cache clears on application restart (in-memory only)

## Migration Notes

### Removed
- `src/modules/SXThalamus/gemini/` - Moved to `src/modules/llm/`
- `src/modules/SXThalamus/exceptions.py` - LLM exceptions moved to `src/modules/llm/`
- Direct `GeminiClient` imports in routes

### Updated
- `SXThalamusService` - Now receives `llm_service` instead of `db_manager`
- `initialize_sxthalamus()` - Takes `llm_service` parameter
- `conversations.py` - Uses `app.state.llm_service`

### Unchanged
- `basic-agent/` - Not currently used, can be updated when needed
- User config structure in database
- Prompt builders and handlers

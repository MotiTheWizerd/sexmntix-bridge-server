# SXThalamus - Next Steps Quick Reference

## 🎯 Immediate Priority: Implement Semantic Grouping

### Step 1: Design the Grouping Prompt (30 min)

**File**: `src/modules/SXThalamus/service.py` (method `_build_default_prompt`)

**Update the prompt to**:
```python
def _build_default_prompt(self, message: str) -> str:
    return f"""Analyze this AI conversation and semantically group the content for intelligent chunking.

Your task:
1. Identify distinct topics/themes in the conversation
2. Group related content together
3. Suggest chunk boundaries based on semantic coherence
4. Provide a brief summary for each group

Return your response as JSON with this structure:
{{
  "groups": [
    {{
      "topic": "Main topic name",
      "summary": "Brief summary of this semantic group",
      "key_points": ["point 1", "point 2"],
      "chunk_boundaries": [
        {{
          "start_marker": "Start phrase or index",
          "end_marker": "End phrase or index",
          "content_preview": "First 100 chars..."
        }}
      ]
    }}
  ],
  "metadata": {{
    "total_groups": 3,
    "suggested_chunks": 5
  }}
}}

Conversation to analyze:
{message}
"""
```

### Step 2: Test with Real Data (30 min)

**Create test script**: `tests/manual/test_semantic_grouping.py`

```python
import asyncio
from src.modules.SXThalamus.service import SXThalamusService
from src.modules.SXThalamus.config import SXThalamusConfig
from src.modules.core.event_bus.event_bus import EventBus
from src.modules.core.telemetry.logger import Logger

async def test_grouping():
    # Setup
    event_bus = EventBus()
    logger = Logger("test")
    config = SXThalamusConfig.from_env()
    service = SXThalamusService(event_bus, logger, config)

    # Sample conversation
    test_message = """
    user: How do I implement authentication in my app?

    assistant: I'll help you implement authentication. First, let's set up
    user authentication with JWT tokens. Here's the basic flow:
    1. User sends credentials
    2. Server validates and returns JWT
    3. Client stores JWT
    4. Client sends JWT with each request

    Here's the code for the authentication endpoint...
    [code block]

    Now for the middleware to verify tokens...
    [code block]

    user: What about password hashing?

    assistant: Great question! For password security, you should use bcrypt...
    """

    # Process
    result = await service.process_message(test_message)

    # Print result
    print("=" * 80)
    print("SEMANTIC GROUPING RESULT:")
    print("=" * 80)
    print(result)
    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(test_grouping())
```

**Run**:
```bash
python tests/manual/test_semantic_grouping.py
```

### Step 3: Parse and Validate LLM Response (1 hour)

**File**: `src/modules/SXThalamus/service.py`

**Add new method**:
```python
def _parse_semantic_groups(self, llm_response: str) -> Dict[str, Any]:
    """
    Parse semantic grouping response from LLM.

    Args:
        llm_response: JSON string from LLM

    Returns:
        Parsed semantic groups with validation

    Raises:
        QwenExecutionError: If response is malformed
    """
    try:
        import json
        data = json.loads(llm_response)

        # Validate structure
        if "groups" not in data:
            raise ValueError("Missing 'groups' key in response")

        groups = data["groups"]

        # Validate each group
        for group in groups:
            required_keys = ["topic", "summary", "chunk_boundaries"]
            for key in required_keys:
                if key not in group:
                    raise ValueError(f"Missing '{key}' in group: {group}")

        self.logger.info(
            "Parsed semantic groups successfully",
            extra={
                "group_count": len(groups),
                "total_chunks": sum(len(g.get("chunk_boundaries", [])) for g in groups)
            }
        )

        return data

    except json.JSONDecodeError as e:
        self.logger.error(f"Failed to parse JSON response: {e}")
        # Fallback: treat as plain text
        return {
            "groups": [{
                "topic": "Unparsed Content",
                "summary": "LLM returned non-JSON response",
                "content": llm_response
            }]
        }
    except Exception as e:
        self.logger.error(f"Error parsing semantic groups: {e}")
        raise QwenExecutionError(f"Failed to parse semantic groups: {e}")
```

**Update `handle_conversation_stored` method** to use this parser:
```python
# After line 165 (after process_message call)
# Parse the semantic groups
semantic_groups = self._parse_semantic_groups(processed_result)

self.logger.info(
    "Semantic grouping completed",
    extra={
        "conversation_id": conversation_id,
        "groups": len(semantic_groups.get("groups", [])),
        "first_topic": semantic_groups["groups"][0]["topic"] if semantic_groups.get("groups") else None
    }
)
```

---

## 🗄️ Step 4: Design Storage Schema (Decision Required)

### Option A: Metadata-based (RECOMMENDED for MVP)

**Advantages**:
- Simple implementation
- No schema changes
- Works with existing ChromaDB collection

**Implementation**:
```python
# In handle_conversation_stored, after parsing groups:
for group_idx, group in enumerate(semantic_groups["groups"]):
    for chunk_idx, chunk in enumerate(group["chunk_boundaries"]):
        metadata = {
            "conversation_id": conversation_id,
            "user_id": user_id,
            "project_id": project_id,
            "semantic_group": group["topic"],
            "group_index": group_idx,
            "chunk_index": chunk_idx,
            "group_summary": group["summary"],
            "total_groups": len(semantic_groups["groups"]),
            "chunk_type": "semantic"  # vs "full_conversation"
        }

        # Store in ChromaDB with this metadata
        # (Implementation in Phase 2)
```

### Option B: Separate Collection

**Create**: `conversation_chunks` collection in ChromaDB

**Schema**:
- `id`: `{conversation_id}_chunk_{idx}`
- `document`: Chunk content
- `embedding`: Vector embedding
- `metadata`:
  - `conversation_id`
  - `parent_conversation_id`
  - `semantic_group`
  - `chunk_index`
  - `group_summary`

---

## 🔄 Step 5: Integrate with Storage (2-3 hours)

### File: `src/modules/SXThalamus/service.py`

**Add method**:
```python
async def _store_semantic_chunks(
    self,
    conversation_id: str,
    user_id: int,
    project_id: str,
    semantic_groups: Dict[str, Any]
):
    """
    Store semantic chunks in ChromaDB.

    Args:
        conversation_id: Conversation UUID
        user_id: User ID
        project_id: Project ID
        semantic_groups: Parsed semantic groups from LLM
    """
    # TODO: Get VectorStorageOrchestrator instance
    # (needs to be injected in __init__)

    for group_idx, group in enumerate(semantic_groups["groups"]):
        topic = group["topic"]
        summary = group["summary"]

        for chunk_idx, chunk in enumerate(group.get("chunk_boundaries", [])):
            # Extract chunk content
            chunk_content = chunk.get("content_preview", "")

            # Build metadata
            metadata = {
                "conversation_id": conversation_id,
                "semantic_group": topic,
                "group_index": group_idx,
                "chunk_index": chunk_idx,
                "group_summary": summary,
                "chunk_type": "semantic"
            }

            # Store via VectorStorageOrchestrator
            # await self.vector_storage.store_chunk(
            #     content=chunk_content,
            #     metadata=metadata,
            #     user_id=user_id,
            #     project_id=project_id
            # )

            self.logger.debug(
                "Stored semantic chunk",
                extra={
                    "conversation_id": conversation_id,
                    "group": topic,
                    "chunk_index": chunk_idx
                }
            )
```

**Update `__init__` to inject VectorStorageOrchestrator**:
```python
def __init__(
    self,
    event_bus: EventBus,
    logger: Logger,
    vector_storage: VectorStorageOrchestrator,  # ADD THIS
    config: Optional[SXThalamusConfig] = None
):
    self.event_bus = event_bus
    self.logger = logger
    self.vector_storage = vector_storage  # STORE THIS
    self.config = config or SXThalamusConfig.from_env()
    # ...
```

**Update `src/api/app.py` to pass VectorStorageOrchestrator**:
```python
# In lifespan startup:
sxthalamus_service = SXThalamusService(
    event_bus=event_bus,
    logger=logger,
    vector_storage=state.vector_storage,  # ADD THIS
    config=SXThalamusConfig.from_env()
)
```

---

## 📊 Step 6: Add Metrics & Monitoring (1 hour)

**File**: `src/modules/SXThalamus/service.py`

**Track**:
- Processing time per conversation
- Group count distribution
- Chunk count distribution
- LLM success/failure rate
- Average token usage (if available)

**Example**:
```python
import time

async def process_message(self, message: str, prompt: Optional[str] = None) -> str:
    start_time = time.time()

    try:
        result = await self._execute_qwen(prompt)

        processing_time = time.time() - start_time

        self.logger.info(
            "Message processed successfully",
            extra={
                "processing_time_ms": processing_time * 1000,
                "message_length": len(message),
                "result_length": len(result)
            }
        )

        return result
    except Exception as e:
        processing_time = time.time() - start_time
        self.logger.error(
            "Message processing failed",
            extra={
                "processing_time_ms": processing_time * 1000,
                "error": str(e)
            }
        )
        raise
```

---

## 🧪 Step 7: Write Tests (2 hours)

### Create: `tests/modules/sxthalamus/test_service.py`

```python
import pytest
from unittest.mock import AsyncMock, Mock

from src.modules.SXThalamus.service import SXThalamusService
from src.modules.SXThalamus.config import SXThalamusConfig

@pytest.fixture
def service():
    event_bus = Mock()
    logger = Mock()
    vector_storage = AsyncMock()
    config = SXThalamusConfig(enabled=True)

    return SXThalamusService(
        event_bus=event_bus,
        logger=logger,
        vector_storage=vector_storage,
        config=config
    )

@pytest.mark.asyncio
async def test_process_message_returns_result(service):
    # Mock LLM response
    service.qwen_client.execute = AsyncMock(return_value='{"result": "test"}')

    result = await service.process_message("test message")

    assert result == "test"

@pytest.mark.asyncio
async def test_semantic_groups_parsing(service):
    llm_response = """{
        "groups": [
            {
                "topic": "Test Topic",
                "summary": "Test summary",
                "chunk_boundaries": []
            }
        ]
    }"""

    parsed = service._parse_semantic_groups(llm_response)

    assert len(parsed["groups"]) == 1
    assert parsed["groups"][0]["topic"] == "Test Topic"

# Add more tests...
```

**Run**:
```bash
pytest tests/modules/sxthalamus/ -v
```

---

## ✅ Success Criteria

Before moving to next phase:

- [ ] LLM returns structured semantic groups
- [ ] Groups are parsed correctly
- [ ] Chunks are identified with boundaries
- [ ] Storage integration working
- [ ] Tests passing
- [ ] Error handling graceful (fallback to simple chunking)
- [ ] Logging comprehensive
- [ ] Performance acceptable (<5s per conversation)

---

## 🚨 Common Issues & Solutions

### Issue: LLM returns malformed JSON
**Solution**: Add fallback parsing, log warning, use simple chunking

### Issue: Chunks too large/small
**Solution**: Add constraints to prompt ("max 500 chars per chunk")

### Issue: Storage fails
**Solution**: Catch exception, log error, don't fail entire conversation

### Issue: Performance too slow
**Solution**:
- Reduce timeout
- Use faster model (haiku instead of sonnet)
- Process in background task

---

## 📞 Questions to Answer

Before implementing:

1. **What's the max chunk size we want?**
   - Recommendation: 500-1000 characters

2. **What if LLM fails?**
   - Recommendation: Fall back to simple text splitting

3. **Do we embed immediately or batch later?**
   - Recommendation: Batch for performance

4. **What metadata do we need for search?**
   - Minimum: conversation_id, user_id, project_id, semantic_group

5. **How do we handle updates?**
   - Recommendation: Immutable chunks (don't update, create new)

---

## 🎯 Timeline Estimate

| Phase | Time | Priority |
|-------|------|----------|
| Design prompt | 30 min | 🔴 High |
| Test with real data | 30 min | 🔴 High |
| Parse response | 1 hour | 🔴 High |
| Design storage | 1 hour | 🟡 Medium |
| Implement storage | 2-3 hours | 🟡 Medium |
| Add monitoring | 1 hour | 🟢 Low |
| Write tests | 2 hours | 🟡 Medium |

**Total**: ~8-10 hours for full implementation

**MVP (Steps 1-3)**: ~2 hours

---

## 🚀 Quick Start (Next Session)

```bash
# 1. Update the prompt in service.py (_build_default_prompt)
# 2. Create and run test script
python tests/manual/test_semantic_grouping.py

# 3. Verify output structure
# 4. Implement parser (_parse_semantic_groups)
# 5. Update handle_conversation_stored to use parser
# 6. Test end-to-end

# 7. Implement storage (if ready)
# 8. Write tests
```

---

**Ready to start?** Begin with Step 1: Update the grouping prompt!

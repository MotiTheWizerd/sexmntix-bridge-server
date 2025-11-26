from typing import Any, List, Tuple, Optional


def resolve_retrieval(intent_result: dict, query: str) -> Tuple[str, List[str], bool]:
    """
    Determine retrieval strategy, required_memory, and sentinel flag.
    """
    retrieval_strategy = intent_result.get("retrieval_strategy", "none")
    required_memory = intent_result.get("required_memory", []) or []
    sentinel_hit = False

    # If intent says none, switch to world_view to pull recent context
    if retrieval_strategy == "none":
        retrieval_strategy = "world_view"

    # If intent returned no required_memory, seed with query for logging
    if not required_memory:
        required_memory = [query]

    # If any required item contains the no-memory sentinel, treat as no retrieval
    if required_memory and any(_contains_no_memory_sentinel(item) for item in required_memory):
        sentinel_hit = True

    return retrieval_strategy, required_memory, sentinel_hit


def parse_time_iso(value: Any):
    """
    Parse ISO string into naive UTC datetime (or None).
    """
    from datetime import datetime, timezone

    if not value or not isinstance(value, str):
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc).replace(tzinfo=None)
    except Exception:
        return None


def _contains_no_memory_sentinel(text: Optional[str]) -> bool:
    if not text:
        return False
    return "[semantix-memory-block]" in text and "No relevant memories found" in text

import re
from typing import Any, Dict, List, Optional


def normalize_turns(conv: Any) -> List[Dict[str, Any]]:
    """
    Normalize conversation raw_data into user/assistant turn objects with metadata.
    """
    raw = conv.raw_data or {}
    candidates = _extract_candidates(raw)

    turns: List[Dict[str, Any]] = []
    pending_user: Optional[str] = None

    for msg in candidates:
        if not isinstance(msg, dict):
            continue

        role = msg.get("role", "").strip()
        text = _extract_text(msg).strip()
        if not role or not text:
            continue

        timestamp = (
            msg.get("timestamp")
            or msg.get("created_at")
            or (conv.created_at.isoformat() if conv.created_at else None)
        )

        metadata = {
            "timestamp": timestamp,
            "conversation_id": conv.conversation_id,
            "source": "conversation",
        }

        if role == "user":
            pending_user = text
        elif role == "assistant":
            if pending_user is not None:
                turns.append(
                    {"user": pending_user, "assistant": text, "metadata": metadata}
                )
                pending_user = None
            else:
                turns.append({"user": "", "assistant": text, "metadata": metadata})

    if pending_user:
        turns.append(
            {
                "user": pending_user,
                "assistant": "",
                "metadata": {
                    "timestamp": conv.created_at.isoformat() if conv.created_at else None,
                    "conversation_id": conv.conversation_id,
                    "source": "conversation",
                },
            }
        )

    return turns


def _extract_candidates(raw: Any) -> List[Any]:
    candidates = []
    if isinstance(raw, list):
        candidates = raw
    elif isinstance(raw, dict):
        if isinstance(raw.get("conversation"), list):
            candidates = raw["conversation"]
        elif isinstance(raw.get("messages"), list):
            candidates = raw["messages"]
        elif isinstance(raw.get("memory_log"), dict):
            mem_log = raw["memory_log"]
            if isinstance(mem_log.get("conversation"), list):
                candidates = mem_log["conversation"]
    return candidates or []


def _extract_text(msg: Dict[str, Any]) -> str:
    """
    Extract text content from various message shapes.
    """
    if not isinstance(msg, dict):
        return ""
    text = ""
    if msg.get("text"):
        text = str(msg.get("text", ""))
    elif isinstance(msg.get("content"), str):
        text = msg["content"]
    elif isinstance(msg.get("content"), list):
        parts = msg["content"]
        text = " ".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in parts
        )
    elif isinstance(msg.get("parts"), list):
        text = " ".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in msg["parts"]
        )
    return _strip_memory_blocks(text)


def _strip_memory_blocks(text: str) -> str:
    """
    Remove [semantix-memory-block] ... [semantix-end-memory-block] content before use.
    """
    if not text:
        return ""
    return re.sub(
        r"\[semantix-memory-block\].*?\[semantix-end-memory-block\]",
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    ).strip()

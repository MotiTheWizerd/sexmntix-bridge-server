"""
Shared helpers for building embeddable conversation text.
"""

import json
import re
from typing import Any, Dict, List, Optional
from datetime import datetime

try:
    # Optional compression brain
    from src.modules.SXPrefrontal import CompressionBrain  # type: ignore
except Exception:  # pragma: no cover
    CompressionBrain = None  # type: ignore


def build_conversation_embedding_text(
    raw_data: Any,
    created_at: Optional[datetime] = None,
    compression_brain: Optional[Any] = None,
) -> Optional[str]:
    """
    Normalize conversation turns and optionally compress to a semantic unit string.

    Returns:
        String ready for embedding, or None if no usable text.
    """
    turns = _extract_turns(raw_data, created_at)
    if not turns:
        return None

    if compression_brain:
        semantic_units: List[str] = []
        for turn in turns:
            user_text = turn.get("user", "")
            assistant_text = turn.get("assistant", "")
            try:
                compressed = compression_brain.compress(user_text, assistant_text)
                unit = compressed.get("semantic_unit", "").strip()
                if unit:
                    semantic_units.append(unit)
            except Exception:
                continue
        if semantic_units:
            return "\n".join(semantic_units)

    # Fallback: JSON turns
    try:
        return json.dumps(turns, ensure_ascii=False, sort_keys=True)
    except Exception:
        return None


def _extract_turns(raw_data: Any, created_at: Optional[datetime]) -> List[Dict[str, Any]]:
    turns: List[Dict[str, Any]] = []

    raw = raw_data or {}
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

    pending_user: Optional[str] = None
    for msg in candidates:
        if not isinstance(msg, dict):
            continue
        role = msg.get("role", "").strip()
        text = _strip_memory_blocks(_extract_message_text(msg)).strip()
        if not role or not text:
            continue

        timestamp = (
            msg.get("timestamp")
            or msg.get("created_at")
            or (created_at.isoformat() if created_at else None)
        )

        metadata = {
            "timestamp": timestamp,
            "conversation_id": msg.get("conversation_id") or raw.get("conversation_id") if isinstance(raw, dict) else None,
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
                    "timestamp": created_at.isoformat() if created_at else None,
                    "conversation_id": None,
                    "source": "conversation",
                },
            }
        )

    return turns


def _extract_message_text(msg: Dict[str, Any]) -> str:
    if not isinstance(msg, dict):
        return ""
    if isinstance(msg.get("text"), str):
        return msg["text"]
    if isinstance(msg.get("content"), str):
        return msg["content"]
    if isinstance(msg.get("content"), list):
        parts = msg["content"]
        return " ".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in parts
        ).strip()
    if isinstance(msg.get("parts"), list):
        return " ".join(
            part.get("text", "") if isinstance(part, dict) else str(part)
            for part in msg["parts"]
        ).strip()
    return ""


def _strip_memory_blocks(text: str) -> str:
    if not text:
        return ""
    return re.sub(
        r"\[semantix-memory-block\].*?\[semantix-end-memory-block\]",
        "",
        text,
        flags=re.IGNORECASE | re.DOTALL,
    )

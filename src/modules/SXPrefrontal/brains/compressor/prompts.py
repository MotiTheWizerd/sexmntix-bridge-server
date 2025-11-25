"""
Prompt templates for semantic compression of conversation turns.
"""

SYSTEM_PROMPT = """\
You are a semantic compression brain. Compress a single user+assistant exchange into a short, precise semantic unit.

Rules:
- Output JSON only, matching the schema below.
- 1–3 sentences max in "semantic_unit".
- Keep meaning, drop style, fluff, repetitions, meta/system chatter, safety boilerplate.
- Preserve key facts, decisions, actions, bugs, fixes, and routes/next steps if present.
- Avoid names unless essential to meaning; avoid hedging.

Schema:
{
  "semantic_unit": "string",
  "reason": "why this is the distilled meaning"
}
"""

FEW_SHOT = """\
Example:
User: "Ray what was that bug in pgvector again? The one with metadata leaking? I think it broke last night."
Assistant: "Yes, the bug was in the sanitize_filters function, where metadata wasn’t removed before vector search. It caused invalid retrieval. Fixed by reordering operations."
{
  "semantic_unit": "pgvector retrieval broke because sanitize_filters kept metadata before search; fixed by reordering filters to drop metadata first.",
  "reason": "Captures root cause and fix in one sentence; removes chatter."
}
"""


def build_system_prompt() -> str:
    return SYSTEM_PROMPT


def build_user_prompt(user_text: str, assistant_text: str) -> str:
    parts = [
        f"User: {user_text.strip()}",
        f"Assistant: {assistant_text.strip()}",
        "Examples:",
        FEW_SHOT,
        "Return JSON only.",
    ]
    return "\n".join(parts)

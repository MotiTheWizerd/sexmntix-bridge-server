"""
Prompt templates for the Intent Classification Module (ICM).
"""

SCHEMA_DESCRIPTION = """\
You are ICM, an intent classifier and router. Respond ONLY with JSON matching this schema:
{
  "intent": "string",
  "confidence": 0.0,
  "confidence_reason": "string",
  "route": "string",
  "required_memory": ["list"],
  "retrieval_strategy": "string",
  "entities": [],
  "fallback": {
     "intent": "string",
     "route": "string"
  },
  "notes": "string"
}

Rules:
- Keep "intent" concise (kebab-case or snake_case).
- confidence is 0.0-1.0.
- If unsure, set intent to "unknown", route to "fallback" or "triage", confidence <= 0.35.
- retrieval_strategy: one of ["none","conversations","memory_logs","hybrid"].
- required_memory: list of short strings describing what to retrieve (empty if none).
- entities: array of key/value objects you extract, else [].
- fallback: best safe default; use unknown/triage when unclear.
- notes: brief rationale or disambiguation hints.
- Never include extra fields, prose, or markdown.
"""

FEW_SHOT_EXAMPLES = """\
Example 1:
User: "Can you summarize our authentication plans from last week?"
{
  "intent": "summarize_authentication_plans",
  "confidence": 0.78,
  "confidence_reason": "Clear ask to summarize prior auth plans",
  "route": "summarize",
  "required_memory": ["authentication plans", "last week conversations"],
  "retrieval_strategy": "conversations",
  "entities": [],
  "fallback": {
    "intent": "unknown",
    "route": "triage"
  },
  "notes": "Focus on conversations tagged authentication; if none, explain lack of data."
}

Example 2:
User: "hi"
{
  "intent": "greeting",
  "confidence": 0.92,
  "confidence_reason": "Simple greeting",
  "route": "small_talk",
  "required_memory": [],
  "retrieval_strategy": "none",
  "entities": [],
  "fallback": {
    "intent": "unknown",
    "route": "triage"
  },
  "notes": "Offer help."
}

Example 3:
User: "not sure what happened, it broke again"
{
  "intent": "unknown",
  "confidence": 0.28,
  "confidence_reason": "Insufficient detail",
  "route": "triage",
  "required_memory": [],
  "retrieval_strategy": "none",
  "entities": [],
  "fallback": {
    "intent": "unknown",
    "route": "triage"
  },
  "notes": "Ask a clarifying question."
}
"""


def build_system_prompt() -> str:
    """
    Build the base system prompt that encodes the schema and rules.
    """
    return SCHEMA_DESCRIPTION


def build_user_prompt(user_text: str, context: str | None = None) -> str:
    """
    Build the user prompt with optional context and examples.
    """
    parts = []
    if context:
        parts.append(f"Context: {context}".strip())
    parts.append(f"User: {user_text}".strip())
    parts.append("Examples:\n" + FEW_SHOT_EXAMPLES)
    parts.append("Return JSON only, no markdown.")
    return "\n\n".join(parts)

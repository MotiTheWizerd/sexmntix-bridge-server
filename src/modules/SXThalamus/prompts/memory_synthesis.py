"""
Memory synthesis prompt builder.

Converts raw semantic search results into natural language memory summaries.
"""

from typing import List, Dict, Any, Optional
import json


def build_memory_synthesis_prompt(
    search_results: List[Dict[str, Any]],
    query: str = None,
    world_view: Optional[Dict[str, Any]] = None,
    identity: Optional[Dict[str, Any]] = None,
    inject_full_world_view: bool = True,
) -> str:
    """
    Build a prompt for synthesizing search results into natural language memory.

    Takes raw semantic search results and formats them for Gemini to create
    a coherent, natural language memory summary. Optionally injects world view
    context (short-term memory or recent conversation summaries) if available.

    Args:
        search_results: List of search results from vector storage
        query: The original user query that triggered this search (optional)
        world_view: Optional dict containing short_term_memory and recent_conversations

    Returns:
        Formatted prompt for memory synthesis

    Example:
        >>> results = [{"document": {...}, "metadata": {...}, "similarity": 0.85}]
        >>> prompt = build_memory_synthesis_prompt(results, query="What do you know about project X?")
    """
    formatted_results = json.dumps(search_results, indent=2)

    query_context = ""
    if query:
        query_context = f"""
The user is currently asking: "{query}"

"""

    world_view_context = ""
    if isinstance(world_view, dict):
        short_term = world_view.get("short_term_memory")
        if short_term:
            world_view_context += f"Short-term memory summary:\n{short_term}\n\n"

        recents = world_view.get("recent_conversations") or []
        if inject_full_world_view and isinstance(recents, list) and recents:
            lines = []
            for conv in recents[:3]:
                summary = conv.get("summary") or conv.get("snippet") or ""
                created_at = conv.get("created_at") or ""
                if summary:
                    lines.append(f"- ({created_at}) {summary}")
            if lines:
                world_view_context += "Recent conversations:\n" + "\n".join(lines) + "\n\n"

    world_view_section = ""
    if world_view_context:
        world_view_section = f"World view context:\n{world_view_context}"

    identity_context = ""
    if isinstance(identity, dict):
        user_identity = identity.get("user_identity") or {}
        assistant_identity = identity.get("assistant_identity") or {}
        system_policies = identity.get("system_policies") or []
        recent_events = identity.get("recent_profile_events") or []

        def fmt_dict(d: Dict[str, Any]) -> str:
            return "; ".join(f"{k}: {v}" for k, v in d.items() if v)

        lines = []
        if user_identity:
            lines.append("User identity: " + fmt_dict(user_identity))
        if assistant_identity:
            lines.append("Assistant identity: " + fmt_dict(assistant_identity))
        if system_policies:
            lines.append("System policies: " + "; ".join(str(p) for p in system_policies))
        if recent_events:
            lines.append(
                "Recent profile events: " + "; ".join(str(e) for e in recent_events[:5])
            )
        if lines:
            identity_context = "\n".join(lines) + "\n\n"

    identity_section = ""
    if identity_context:
        identity_section = f"Identity context:\n{identity_context}"

    prompt = f"""
You are receiving raw semantic memory results.
Your job is to turn them into ONE clean, human-readable memory entry.

Follow these rules with zero deviation:

CONTENT STYLE:
- Write like a human explaining something in simple words.
- Use short sentences and one idea per paragraph.
- No abstract language. No generic "LLM summary tone".
- Avoid complex phrasing. Avoid metaphors. Avoid compression that loses realism.
- Be concrete, factual, and direct.
- Preserve meaning, not surface wording.

STRUCTURE RULES:
- Start with: "Core Concept: <one clear sentence>"
  - Must express the main idea in plain language.
  - No abstractions or meta-phrases.

- Then write 2-4 short paragraphs beginning with:
  "I remember..."
  - Each paragraph describes one topic only.
  - Use natural, human-like explanation.
  - Do not combine unrelated ideas.
  - Do not compress too much. Keep it readable and grounded.

- End with:
  "Key Association: <one simple sentence>"
  - Explain what connects the memories in plain language.

CONTENT YOU MUST REMOVE:
- timestamps
- metadata
- IDs
- similarity scores
- JSON fields
- technical noise
- quotes from the raw memory

WHAT YOU MUST KEEP:
- the meaning
- the intention
- the factual relationships

FORMATTING:
Your output must EXACTLY follow this pattern:

Core Concept: <sentence>

I remember... <paragraph 1>

I remember... <paragraph 2>

I remember... <paragraph 3> (if needed)

Key Association: <sentence>

Nothing else.
{identity_section}{world_view_section}User query: {query_context}
Raw semantic memory results:
{formatted_results}
"""

    return prompt

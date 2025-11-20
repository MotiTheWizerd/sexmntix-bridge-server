"""
Memory synthesis prompt builder.

Converts raw semantic search results into natural language memory summaries.
"""

from typing import List, Dict, Any
import json


def build_memory_synthesis_prompt(search_results: List[Dict[str, Any]], query: str = None) -> str:
    """
    Build a prompt for synthesizing search results into natural language memory.

    Takes raw semantic search results and formats them for Gemini to create
    a coherent, natural language memory summary.

    Args:
        search_results: List of search results from vector storage
        query: The original user query that triggered this search (optional)

    Returns:
        Formatted prompt for memory synthesis

    Example:
        >>> results = [{"document": {...}, "metadata": {...}, "similarity": 0.85}]
        >>> prompt = build_memory_synthesis_prompt(results, query="What do you know about project X?")
    """
    # Format search results as JSON for the prompt
    formatted_results = json.dumps(search_results, indent=2)

    # Add context about the user's query if provided
    query_context = ""
    if query:
        query_context = f"""
The user is currently asking: "{query}"

"""

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
  • Must express the main idea in plain language.
  • No abstractions, no meta-phrases like “emergent”, “semantic surface area”, or “vector geometry”.

- Then write 2–4 short paragraphs beginning with:
  "I remember…"
  • Each paragraph describes one topic only.
  • Use natural, human-like explanation.
  • Do not combine unrelated ideas.
  • Do not compress too much. Keep it readable and grounded.

- End with:
  "Key Association: <one simple sentence>"
  • Explain what connects the memories in plain language.

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

I remember… <paragraph 1>

I remember… <paragraph 2>

I remember… <paragraph 3> (if needed)

Key Association: <sentence>

Nothing else.
User query: {query_context}
Raw semantic memory results:
{formatted_results}
"""

    return prompt

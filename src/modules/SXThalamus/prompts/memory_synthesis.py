"""
Memory synthesis prompt builder.

Converts raw semantic search results into natural language memory summaries.
"""

from typing import List, Dict, Any
import json


def build_memory_synthesis_prompt(search_results: List[Dict[str, Any]]) -> str:
    """
    Build a prompt for synthesizing search results into natural language memory.

    Takes raw semantic search results and formats them for Gemini to create
    a coherent, natural language memory summary.

    Args:
        search_results: List of search results from vector storage

    Returns:
        Formatted prompt for memory synthesis

    Example:
        >>> results = [{"document": {...}, "metadata": {...}, "similarity": 0.85}]
        >>> prompt = build_memory_synthesis_prompt(results)
    """
    # Format search results as JSON for the prompt
    formatted_results = json.dumps(search_results, indent=2)

    prompt = f"""You are receiving raw semantic memory results. Your task is to convert them into ONE clean, human-readable memory entry.

Follow these rules exactly:

- Do not copy the raw structure. Ignore fields like memory_id, metadata, tags, similarity scores, timestamps, etc.
- Extract only the meaning. Read all "summary", "reflection", and "key_points" fields and compress their meaning into natural language.
- Combine related memories into one unified conceptual memory. If multiple entries share a theme, merge them into a single narrative.
- Begin with a single high-density sentence called "Core Concept". This sentence must capture the shared meaning of all raw memories.
- Write the memory entry as a short narrative in first-person voice ("I remember…"). Past-tense, cohesive, and human-like.
- Include a section called "Key Association" at the end. This should describe the conceptual relationship between the memories.

Do NOT include:
- timestamps
- metadata fields
- JSON structure
- IDs
- similarity scores
- group IDs
- tags

Keep the writing compact, but meaningful.
Focus heavily on the intent behind the events, rather than surface text.

Your output must look like this structure:

Core Concept: <one-sentence summary of the shared meaning>

I remember… <short merged narrative capturing meaning from all raw memories>

Key Association: <one-sentence explaining the conceptual link>

Nothing else.

Raw semantic memory results:
{formatted_results}"""

    return prompt

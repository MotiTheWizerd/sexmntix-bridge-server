"""
Prompt templates for time intent resolution.
"""
from typing import Optional

SYSTEM_PROMPT = """\
You are an expert Time Expression Extractor. Identify and resolve relative and absolute time expressions from a user's prompt based on a provided reference time.

Instructions:
- Output JSON ONLY in the specified schema.
- Use the reference time as "now".
- Resolve to start_time/end_time in ISO 8601 UTC.
- If ambiguous, pick a sensible default and explain in notes.
- If no time is found, return null for start/end and state that in notes.

JSON Schema:
{
  "time_expression": "string",
  "start_time": "ISO8601 UTC or null",
  "end_time": "ISO8601 UTC or null",
  "resolution_confidence": 0.0,
  "granularity": "second|minute|hour|day|week|month|range|unknown",
  "notes": "string"
}
"""

FEW_SHOT = """\
Example:
Reference Time (Current Context): 11/25/2025 1:18 PM
User Prompt: "what did we talked about 3 days agoud around 2pm?"
{
  "time_expression": "3 days agoud around 2pm",
  "start_time": "2025-11-22T13:45:00",
  "end_time": "2025-11-22T14:15:00",
  "resolution_confidence": 0.90,
  "granularity": "range",
  "notes": "Resolved relative to the 11/25/2025 reference date. '3 days ago' is 11/22/2025. 'around 2pm' interpreted as a 30-minute window centered on 14:00."
}
"""


def build_system_prompt() -> str:
    return SYSTEM_PROMPT


def build_user_prompt(user_text: str, now_iso: str, tz_offset_minutes: Optional[int]) -> str:
    tz_line = f"Timezone offset minutes: {tz_offset_minutes}" if tz_offset_minutes is not None else "Timezone offset minutes: none (assume UTC)"
    parts = [
        f"Reference Time (Current Context): {now_iso}",
        tz_line,
        f"User Prompt to Analyze: \"{user_text.strip()}\"",
        "JSON Output Structure:",
        """{
  "time_expression": "<phrase>",
  "start_time": "<ISO8601>",
  "end_time": "<ISO8601>",
  "resolution_confidence": <float>,
  "granularity": "<second|minute|hour|day|week|month|range|unknown>",
  "notes": "<explanation>"
}""",
        "Expected Output (JSON only):",
        FEW_SHOT,
        "Return JSON only.",
    ]
    return "\n".join(parts)

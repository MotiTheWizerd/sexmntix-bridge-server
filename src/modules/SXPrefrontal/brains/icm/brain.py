import json
from typing import Any, Dict, Optional

from src.modules.SXPrefrontal.model import SXPrefrontalModel
from . import prompts


DEFAULT_RESPONSE = {
    "intent": "unknown",
    "confidence": 0.0,
    "confidence_reason": "Unable to determine intent",
    "route": "triage",
    "required_memory": [],
    "retrieval_strategy": "none",
    "entities": [],
    "fallback": {
        "intent": "unknown",
        "route": "triage"
    },
    "notes": ""
}


class ICMBrain:
    """
    Intent Classification Module built on SXPrefrontal (Qwen).
    """

    def __init__(self, model: Optional[SXPrefrontalModel] = None):
        self.model = model or SXPrefrontalModel()

    def classify(self, text: str, context: Optional[str] = None) -> Dict[str, Any]:
        """
        Classify user text into the intent schema.
        """
        system_prompt = prompts.build_system_prompt()
        user_prompt = prompts.build_user_prompt(text, context)

        try:
            raw = self.model.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=600,
                temperature=0.3
            )
            parsed = self._parse_json(raw)
            return self._normalize(parsed)
        except Exception:
            return DEFAULT_RESPONSE.copy()

    def _parse_json(self, raw: str) -> Dict[str, Any]:
        """
        Parse JSON from model output; raise on failure.
        """
        raw = raw.strip()
        # Handle fenced blocks defensively
        if raw.startswith("```"):
            raw = raw.strip("`").strip()
            if raw.lower().startswith("json"):
                raw = raw[4:].strip()
        return json.loads(raw)

    def _normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Ensure all expected keys exist with defaults.
        """
        normalized = DEFAULT_RESPONSE.copy()
        normalized.update({
            "intent": data.get("intent", normalized["intent"]),
            "confidence": data.get("confidence", normalized["confidence"]),
            "confidence_reason": data.get("confidence_reason", normalized["confidence_reason"]),
            "route": data.get("route", normalized["route"]),
            "required_memory": data.get("required_memory", normalized["required_memory"]),
            "retrieval_strategy": data.get("retrieval_strategy", normalized["retrieval_strategy"]),
            "entities": data.get("entities", normalized["entities"]),
            "fallback": data.get("fallback", normalized["fallback"]),
            "notes": data.get("notes", normalized["notes"])
        })
        return normalized

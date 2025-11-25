import json
from typing import Any, Dict, Optional

from src.modules.SXPrefrontal.model import SXPrefrontalModel
from . import prompts


DEFAULT_OUTPUT = {
    "semantic_unit": "",
    "reason": "failed to compress",
}


class CompressionBrain:
    """
    Compresses a user+assistant pair into a short semantic unit (1–3 sentences).
    """

    def __init__(self, model: Optional[SXPrefrontalModel] = None):
        self.model = model or SXPrefrontalModel()

    def compress(self, user_text: str, assistant_text: str) -> Dict[str, Any]:
        system_prompt = prompts.build_system_prompt()
        user_prompt = prompts.build_user_prompt(user_text, assistant_text)

        try:
            raw = self.model.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=300,
                temperature=0.2,
            )
            parsed = self._parse_json(raw)
            return self._normalize(parsed)
        except Exception:
            return DEFAULT_OUTPUT.copy()

    def _parse_json(self, raw: str) -> Dict[str, Any]:
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.strip("`").strip()
            if raw.lower().startswith("json"):
                raw = raw[4:].strip()
        return json.loads(raw)

    def _normalize(self, data: Dict[str, Any]) -> Dict[str, Any]:
        normalized = DEFAULT_OUTPUT.copy()
        normalized.update({
            "semantic_unit": data.get("semantic_unit", "").strip(),
            "reason": data.get("reason", normalized["reason"]).strip(),
        })
        return normalized

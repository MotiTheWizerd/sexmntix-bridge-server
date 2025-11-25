import json
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from src.modules.SXPrefrontal.model import SXPrefrontalModel
from . import prompts


DEFAULT_OUTPUT = {
    "time_expression": "",
    "start_time": None,
    "end_time": None,
    "resolution_confidence": 0.2,
    "granularity": "unknown",
    "notes": "failed to resolve",
}


class TimeICMBrain:
    """
    Resolves time expressions to start/end windows in UTC.
    """

    def __init__(self, model: Optional[SXPrefrontalModel] = None):
        self.model = model or SXPrefrontalModel()

    def resolve(self, text: str, now: Optional[datetime] = None, tz_offset_minutes: Optional[int] = None) -> Dict[str, Any]:
        now = now or datetime.now(timezone.utc)
        if now.tzinfo is None:
            now = now.replace(tzinfo=timezone.utc)

        system_prompt = prompts.build_system_prompt()
        user_prompt = prompts.build_user_prompt(
            user_text=text,
            now_iso=now.isoformat(),
            tz_offset_minutes=tz_offset_minutes
        )

        try:
            raw = self.model.generate(
                prompt=user_prompt,
                system_prompt=system_prompt,
                max_tokens=300,
                temperature=0.2,
            )
            parsed = self._parse_json(raw)
            normalized = self._normalize(parsed, now=now, tz_offset_minutes=tz_offset_minutes, original_text=text)
            return normalized
        except Exception:
            return DEFAULT_OUTPUT.copy()

    def _parse_json(self, raw: str) -> Dict[str, Any]:
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw.strip("`").strip()
            if raw.lower().startswith("json"):
                raw = raw[4:].strip()
        return json.loads(raw)

    def _normalize(self, data: Dict[str, Any], now: datetime, tz_offset_minutes: Optional[int], original_text: str) -> Dict[str, Any]:
        out = DEFAULT_OUTPUT.copy()
        out.update({
            "time_expression": data.get("time_expression", "").strip(),
            "start_time": data.get("start_time"),
            "end_time": data.get("end_time"),
            "resolution_confidence": data.get("resolution_confidence", out["resolution_confidence"]),
            "granularity": data.get("granularity", out["granularity"]),
            "notes": data.get("notes", out["notes"]),
        })

        # If LLM left expression empty, use original text for fallback detection
        if not out["time_expression"]:
            out["time_expression"] = original_text.strip()

        return out

    def _last_night_window(self, now: datetime, tz_offset_minutes: Optional[int]) -> tuple[datetime, datetime]:
        if tz_offset_minutes is not None:
            tz = timezone(timedelta(minutes=tz_offset_minutes))
            now = now.astimezone(tz)
        evening_start = now.replace(hour=18, minute=0, second=0, microsecond=0)
        morning_end = now.replace(hour=4, minute=0, second=0, microsecond=0)
        if now.time() < morning_end.timetz():
            start = evening_start - timedelta(days=1)
            end = now
        else:
            start = evening_start - timedelta(days=1)
            end = morning_end
        return start.astimezone(timezone.utc), end.astimezone(timezone.utc)

"""
Identity ICM service.

Provides a lightweight, always-on identity profile for a given user/project.
Designed to be fetched unconditionally at conversation start so the AI
never replies without basic user/assistant context.
"""

import json
from typing import Any, Dict, Optional

from src.modules.core import Logger


class IdentityICMService:
    """
    Returns an identity payload for a user/project.

    Currently backed by environment/config payloads; can be extended to
    persist profiles in the database later. The service never returns None:
    it always emits a minimal skeleton so the prompt can include an identity
    section even when no profile is configured.
    """

    def __init__(self, logger: Optional[Logger] = None, identity_json: Optional[str] = None):
        self.logger = logger
        self.identity_json = identity_json

    def get_identity(self, user_id: Optional[str], project_id: Optional[str]) -> Dict[str, Any]:
        # Try to parse configured identity JSON blob if provided
        if self.identity_json:
            try:
                parsed = json.loads(self.identity_json)
                return self._with_metadata(parsed, user_id, project_id)
            except Exception as e:
                if self.logger:
                    self.logger.warning(
                        "[IDENTITY_ICM] failed to parse configured identity_json",
                        extra={"error": str(e)},
                    )

        # Fallback minimal identity skeleton
        return self._with_metadata(
            {
                "user_identity": {
                    "role": "user",
                    "goals": [],
                    "preferences": [],
                    "constraints": [],
                    "tone": "concise and clear",
                },
                "assistant_identity": {
                    "role": "assistant",
                    "style": "helpful, direct, precise",
                    "safety": "respect privacy; avoid hallucination; ask before assuming",
                },
                "system_policies": [],
                "recent_profile_events": [],
            },
            user_id,
            project_id,
        )

    def _with_metadata(self, payload: Dict[str, Any], user_id: Optional[str], project_id: Optional[str]) -> Dict[str, Any]:
        payload = dict(payload or {})
        payload.setdefault("user_id", user_id)
        payload.setdefault("project_id", project_id)
        return payload

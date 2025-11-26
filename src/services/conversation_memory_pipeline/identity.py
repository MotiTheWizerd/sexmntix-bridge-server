from typing import Any, Dict, Optional
from src.modules.core import Logger
from src.services.identity_service import IdentityICMService


def compute_identity(
    identity_service: IdentityICMService,
    user_id: Optional[str],
    project_id: Optional[str],
    logger: Optional[Logger],
) -> Optional[Dict[str, Any]]:
    try:
        return identity_service.get_identity(user_id=user_id, project_id=project_id)
    except Exception as e:
        if logger:
            logger.warning(
                "[FETCH_MEMORY_PIPELINE] failed to compute identity",
                extra={"error": str(e), "user_id": user_id, "project_id": project_id},
            )
        return None

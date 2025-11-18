"""
Storage Path Management

Handles storage path computation and directory creation for ChromaDB.
"""

import os
from pathlib import Path
from typing import Optional
from src.modules.core.telemetry.logger import get_logger

logger = get_logger(__name__)


class StoragePathManager:
    """
    Manages ChromaDB storage paths for single shared instance.

    Features:
    - Single base path for all users/projects (collection-based isolation)
    - Automatic directory creation
    - Path validation and logging

    Note: User/project isolation is now handled via ChromaDB collection naming,
    not physical path separation.
    """

    def __init__(self, base_path: str = "./data/chromadb"):
        """
        Initialize storage path manager.

        Args:
            base_path: Base directory for ChromaDB storage (default: ./data/chromadb)
        """
        self.base_path = base_path
        self.logger = logger

    def get_path(
        self,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> str:
        """
        Get the storage path (always returns base path).

        Args:
            user_id: Ignored (kept for backward compatibility)
            project_id: Ignored (kept for backward compatibility)

        Returns:
            Base storage path (shared by all users/projects)

        Note: User/project parameters are ignored. All users share the same
        ChromaDB instance with isolation via collection naming.
        """
        # Always return base path (no nesting)
        return self.base_path

    def ensure_path_exists(
        self,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> str:
        """
        Ensure storage path exists, creating directories as needed.

        Args:
            user_id: Ignored (kept for backward compatibility)
            project_id: Ignored (kept for backward compatibility)

        Returns:
            Base storage path that now exists

        Note: Always creates/returns the base path, regardless of user_id/project_id.
        """
        path = self.get_path(user_id, project_id)
        os.makedirs(path, exist_ok=True)

        self.logger.debug(f"[STORAGE_MANAGER] Ensured storage path exists: {path}")

        return path

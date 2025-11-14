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
    Manages ChromaDB storage paths with support for multi-tenant isolation.

    Features:
    - Nested path structure: {base}/{user_id}/{project_id}
    - Automatic directory creation
    - Path validation and logging
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
        Get the storage path, optionally with user/project nesting.

        Args:
            user_id: Optional user ID for nested directory
            project_id: Optional project ID for nested directory

        Returns:
            Full storage path

        Raises:
            ValueError: If only one of user_id/project_id is provided
        """
        # Validate that both or neither user_id/project_id are provided
        if (user_id is None) != (project_id is None):
            raise ValueError(
                "Both user_id and project_id must be provided together, or neither"
            )

        # Build nested path if user_id/project_id provided
        if user_id and project_id:
            path = str(Path(self.base_path) / user_id / project_id)
        else:
            path = self.base_path

        return path

    def ensure_path_exists(
        self,
        user_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> str:
        """
        Ensure storage path exists, creating directories as needed.

        Args:
            user_id: Optional user ID for nested directory
            project_id: Optional project ID for nested directory

        Returns:
            Full storage path that now exists

        Raises:
            ValueError: If only one of user_id/project_id is provided
        """
        path = self.get_path(user_id, project_id)
        os.makedirs(path, exist_ok=True)

        self.logger.debug(f"[STORAGE_MANAGER] Ensured storage path exists: {path}")

        return path

"""
ChromaDB Storage Repository

Handles file system operations for ChromaDB storage.
Extracts file system logic from route handlers.
"""

from pathlib import Path
from typing import Optional

from src.infrastructure.chromadb.client import ChromaDBClient
from src.api.schemas.chromadb_viewer import StorageNode, StorageTreeResponse


class StorageRepository:
    """Repository for ChromaDB storage operations"""

    def __init__(self, chromadb_client: ChromaDBClient):
        self.chromadb_client = chromadb_client

    def get_storage_tree(self) -> StorageTreeResponse:
        """
        Get the ChromaDB storage directory tree structure.

        Returns:
            Directory tree with file sizes and structure
        """
        base_path = self.chromadb_client.base_storage_path

        # Build tree
        tree = self._build_tree(base_path)
        total_size = self._calculate_total_size(tree)

        return StorageTreeResponse(
            base_path=base_path,
            total_size=total_size,
            tree=tree
        )

    def _build_tree(self, path: str) -> StorageNode:
        """
        Recursively build directory tree.

        Args:
            path: Path to build tree from

        Returns:
            StorageNode representing the path
        """
        path_obj = Path(path)

        if path_obj.is_file():
            return StorageNode(
                name=path_obj.name,
                path=str(path_obj),
                type="file",
                size=path_obj.stat().st_size,
                children=None
            )
        elif path_obj.is_dir():
            children = []
            try:
                for child in sorted(path_obj.iterdir()):
                    children.append(self._build_tree(str(child)))
            except PermissionError:
                pass

            return StorageNode(
                name=path_obj.name if path_obj.name else "chromadb",
                path=str(path_obj),
                type="directory",
                size=None,
                children=children if children else None
            )
        else:
            return StorageNode(
                name=path_obj.name,
                path=str(path_obj),
                type="unknown",
                size=None,
                children=None
            )

    def _calculate_total_size(self, node: StorageNode) -> int:
        """
        Calculate total size recursively.

        Args:
            node: StorageNode to calculate size for

        Returns:
            Total size in bytes
        """
        if node.type == "file" and node.size:
            return node.size
        elif node.children:
            return sum(self._calculate_total_size(child) for child in node.children)
        return 0

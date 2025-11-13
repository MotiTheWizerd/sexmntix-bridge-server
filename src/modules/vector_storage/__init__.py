"""
Vector Storage Module

Provides semantic search capabilities through embedding generation and vector storage.
Organized into single-responsibility components:
- text_extraction: Extract searchable text from data structures
- storage: Handle vector storage operations
- search: Semantic search and similarity filtering
- models: Data transfer objects and result models
"""

from src.modules.vector_storage.service import VectorStorageService

__all__ = ["VectorStorageService"]

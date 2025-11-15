"""
Collection Management Module

Provides collection management functionality split into focused components:
- cache: Collection caching layer
- operations: Core CRUD operations
- manager: Facade coordinating cache and operations
"""

from .manager import CollectionManager

__all__ = ["CollectionManager"]

"""Operations for ChromaDB infrastructure.

Modules:
- memory: Memory CRUD operations (refactored into sub-components)
- memory_operations: Deprecated - kept for backward compatibility
- search_operations: Search operations
"""

from . import memory, memory_operations, search_operations
from .memory import (
    create_memory,
    read_memory,
    delete_memory,
    count_memories,
    # Backward compatibility aliases
    add_memory,
    get_by_id,
    delete,
    count,
    # Builder and logger functions
    extract_document_summary,
    build_memory_document,
    get_content_preview,
    log_memory_addition,
    log_memory_retrieval,
    log_memory_deletion
)

__all__ = [
    # Modules
    "memory",
    "memory_operations",  # Deprecated
    "search_operations",
    # CRUD operations (primary names)
    "create_memory",
    "read_memory",
    "delete_memory",
    "count_memories",
    # Backward compatibility aliases
    "add_memory",
    "get_by_id",
    "delete",
    "count",
    # Builder and logger functions
    "extract_document_summary",
    "build_memory_document",
    "get_content_preview",
    "log_memory_addition",
    "log_memory_retrieval",
    "log_memory_deletion"
]

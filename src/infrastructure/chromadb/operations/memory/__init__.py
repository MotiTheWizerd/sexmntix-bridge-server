"""Memory Operations Module

Provides CRUD operations for memory storage and retrieval in ChromaDB.

Sub-components:
- crud: Core database operations (create, read, delete, count)
- document_builder: Document transformation and field extraction
- memory_logger: Logging utilities for memory operations
"""

from .crud import (
    create_memory,
    read_memory,
    delete_memory,
    count_memories
)
from .document_builder import (
    extract_document_summary,
    build_memory_document,
    get_content_preview
)
from .memory_logger import (
    log_memory_addition,
    log_memory_retrieval,
    log_memory_deletion
)

# Backward compatibility aliases
add_memory = create_memory
get_by_id = read_memory
delete = delete_memory
count = count_memories

__all__ = [
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
    # Document builder functions
    "extract_document_summary",
    "build_memory_document",
    "get_content_preview",
    # Logger functions
    "log_memory_addition",
    "log_memory_retrieval",
    "log_memory_deletion"
]

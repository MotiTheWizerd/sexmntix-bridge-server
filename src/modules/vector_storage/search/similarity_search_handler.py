"""
Similarity Search Handler (Backward Compatibility Wrapper)

DEPRECATED: This module has been refactored into the handler/ package.
This file now re-exports from the new modules for backward compatibility.

For new code, import directly from:
    from src.modules.vector_storage.search.handler import BaseSearchHandler, SearchRequest, SearchResponse

The new structure provides better separation of concerns:
- handler/models.py: Data models (SearchRequest, SearchResponse)
- handler/formatters.py: Result formatting utilities
- handler/telemetry.py: Event publishing and logging
- handler/orchestrator.py: Search workflow orchestration
- handler/base_handler.py: Main handler class

Benefits of the new structure:
- Single Responsibility: Each component has a clear, focused purpose
- Testability: Components can be tested in isolation
- Extensibility: Easy to add new features or modify existing behavior
- Maintainability: Changes are localized to specific components
"""

# Re-export from handler package for backward compatibility
from src.modules.vector_storage.search.handler import BaseSearchHandler

# Alias for backward compatibility
SimilaritySearchHandler = BaseSearchHandler

__all__ = ["SimilaritySearchHandler"]

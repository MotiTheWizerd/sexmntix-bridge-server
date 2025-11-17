"""
Memory Search Result Module

Provides dataclass and utilities for memory search results.

Public API:
    MemorySearchResult - Main dataclass for search results

Utilities (advanced usage):
    validators - Validation functions
    serializers - Serialization utilities
    factory - Factory methods
"""

from .model import MemorySearchResult

# Export main model
__all__ = ["MemorySearchResult"]

# Utilities are importable but not in __all__ (advanced users only)
from . import validators
from . import serializers
from . import factory

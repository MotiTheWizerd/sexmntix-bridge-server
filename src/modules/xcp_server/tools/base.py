"""
Base Tool Interface for XCP Server

DEPRECATED: This module has been refactored into the base/ package.
This file now re-exports from the new modules for backward compatibility.

For new code, import directly from:
    from src.modules.xcp_server.tools.base import BaseTool, ToolDefinition, ToolParameter, ToolResult

The new structure provides better separation of concerns:
- base/models.py: Data models
- base/validation.py: Argument validation
- base/telemetry.py: Event publishing and logging
- base/execution.py: Execution orchestration
- base/base_tool.py: Abstract base class
"""

# Re-export public API from new modules for backward compatibility
from src.modules.xcp_server.tools.base import (
    ToolParameter,
    ToolDefinition,
    ToolResult,
    BaseTool
)

__all__ = [
    "ToolParameter",
    "ToolDefinition",
    "ToolResult",
    "BaseTool"
]

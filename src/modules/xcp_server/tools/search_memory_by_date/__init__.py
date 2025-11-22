"""
Search memory by date MCP tool

Simple HTTP proxy that forwards date-filtered search requests to the backend API.
"""

from src.modules.xcp_server.tools.search_memory_by_date.tool import SearchMemoryByDateTool

__all__ = ["SearchMemoryByDateTool"]

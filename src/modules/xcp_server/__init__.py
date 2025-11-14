"""
XCPServer Module - MCP (Model Context Protocol) Server Implementation

This module provides an MCP server that exposes semantic memory and vector storage
capabilities to AI assistants through standardized tools and resources.
"""

from .service.xcp_server_service import XCPServerService

__all__ = ["XCPServerService"]

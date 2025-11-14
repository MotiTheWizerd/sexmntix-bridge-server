"""
Dependency injection for XCP server service.
"""

from fastapi import Request
from src.modules.xcp_server import XCPServerService


def get_xcp_server_service(request: Request) -> XCPServerService:
    """
    Get the XCP server service instance from application state.

    Args:
        request: FastAPI request object

    Returns:
        XCPServerService instance
    """
    return request.app.state.xcp_server_service

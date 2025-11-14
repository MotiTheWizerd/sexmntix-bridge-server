"""
XCPServer Configuration Models

Pydantic models for XCP server configuration loaded from environment variables.
"""

import os
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()


class TransportType(str, Enum):
    """Supported transport types for MCP communication"""
    STDIO = "stdio"
    SSE = "sse"


class LogLevel(str, Enum):
    """Log levels for XCP server"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"


class XCPConfig(BaseModel):
    """XCP Server Configuration

    Configuration loaded from environment variables with sensible defaults.
    """

    # Server identification
    server_name: str = Field(
        default_factory=lambda: os.getenv("XCP_SERVER_NAME", "semantic-bridge-mcp"),
        description="Server name displayed to MCP clients"
    )

    server_version: str = Field(
        default_factory=lambda: os.getenv("XCP_SERVER_VERSION", "1.0.0"),
        description="Server version"
    )

    # Server control
    enabled: bool = Field(
        default_factory=lambda: os.getenv("XCP_SERVER_ENABLED", "true").lower() == "true",
        description="Enable/disable the XCP server"
    )

    # Transport configuration
    transport: TransportType = Field(
        default_factory=lambda: TransportType(os.getenv("XCP_TRANSPORT", "stdio")),
        description="Transport method (stdio or sse)"
    )

    # Default context
    default_user_id: int = Field(
        default_factory=lambda: int(os.getenv("XCP_DEFAULT_USER_ID", "1")),
        description="Default user ID for operations"
    )

    default_project_id: str = Field(
        default_factory=lambda: os.getenv("XCP_DEFAULT_PROJECT_ID", "default"),
        description="Default project ID for operations"
    )

    # Logging
    log_level: LogLevel = Field(
        default_factory=lambda: LogLevel(os.getenv("XCP_LOG_LEVEL", "info")),
        description="Log level for XCP server"
    )

    class Config:
        """Pydantic configuration"""
        use_enum_values = True


class ToolContext(BaseModel):
    """Context for tool execution

    Encapsulates user and project context for tool operations.
    Can be overridden per tool call.
    """

    user_id: int = Field(
        description="User ID for this operation"
    )

    project_id: str = Field(
        description="Project ID for this operation"
    )

    session_id: Optional[str] = Field(
        default=None,
        description="Optional session identifier"
    )


def load_xcp_config() -> XCPConfig:
    """Load XCP configuration from environment

    Returns:
        XCPConfig: Validated configuration object
    """
    return XCPConfig()

"""
XCPServer Configuration Models

Pydantic models for XCP server configuration loaded from environment variables.
"""

import os
from enum import Enum
from typing import Optional
from pathlib import Path
from pydantic import BaseModel, Field
from dotenv import load_dotenv

# Load .env from the project root (where this code lives)
# This ensures .env is found even when config is imported from anywhere
# Path: config.py -> models/ -> xcp_server/ -> modules/ -> src/ -> project_root/
project_root = Path(__file__).parent.parent.parent.parent.parent
dotenv_path = project_root / ".env"
load_dotenv(dotenv_path=dotenv_path, override=False)  # Preserve env vars from .mcp.json


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


    # Logging
    log_level: LogLevel = Field(
        default_factory=lambda: LogLevel(os.getenv("XCP_LOG_LEVEL", "info")),
        description="Log level for XCP server"
    )

    # Temporal reranking configuration
    enable_temporal_decay: bool = Field(
        default_factory=lambda: os.getenv("XCP_TEMPORAL_DECAY_ENABLED", "false").lower() == "true",
        description="Enable temporal decay reranking by default"
    )

    temporal_half_life_days: float = Field(
        default_factory=lambda: float(os.getenv("XCP_TEMPORAL_HALF_LIFE_DAYS", "30")),
        description="Default half-life in days for exponential decay"
    )

    # SSE Transport configuration
    sse_host: str = Field(
        default_factory=lambda: os.getenv("XCP_SSE_HOST", "localhost"),
        description="Host to bind SSE server to"
    )

    sse_port: int = Field(
        default_factory=lambda: int(os.getenv("XCP_SSE_PORT", "3001")),
        description="Port for SSE server"
    )

    class Config:
        """Pydantic configuration"""
        use_enum_values = True


class ToolContext(BaseModel):
    """Context for tool execution

    Minimal context for tool operations. Tools receive user_id and project_id
    as explicit parameters from the client.
    """

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

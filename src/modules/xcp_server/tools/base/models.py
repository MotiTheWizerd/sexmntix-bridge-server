"""
Data models for XCP tool system

Pure data structures with no business logic dependencies.
Provides Pydantic models for tool parameters, definitions, and results.
"""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ToolParameter(BaseModel):
    """Definition of a tool parameter"""
    name: str = Field(description="Parameter name")
    type: str = Field(description="Parameter type (string, number, boolean, object, array)")
    description: str = Field(description="Human-readable parameter description")
    required: bool = Field(default=False, description="Whether this parameter is required")
    default: Optional[Any] = Field(default=None, description="Default value if not provided")
    enum: Optional[List[Any]] = Field(default=None, description="List of allowed values")


class ToolDefinition(BaseModel):
    """MCP tool definition"""
    name: str = Field(description="Unique tool identifier")
    description: str = Field(description="Human-readable tool description")
    parameters: List[ToolParameter] = Field(default_factory=list, description="Tool parameters")

    def to_mcp_schema(self) -> Dict[str, Any]:
        """Convert to MCP tool schema format

        Returns:
            Dict[str, Any]: MCP-compatible tool schema
        """
        properties = {}
        required = []

        for param in self.parameters:
            param_schema = {
                "type": param.type,
                "description": param.description
            }

            if param.enum:
                param_schema["enum"] = param.enum

            if param.default is not None:
                param_schema["default"] = param.default

            properties[param.name] = param_schema

            if param.required:
                required.append(param.name)

        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }


class ToolResult(BaseModel):
    """Result of tool execution"""
    success: bool = Field(description="Whether execution was successful")
    data: Any = Field(default=None, description="Result data")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    error_code: Optional[str] = Field(default=None, description="Error code if failed")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

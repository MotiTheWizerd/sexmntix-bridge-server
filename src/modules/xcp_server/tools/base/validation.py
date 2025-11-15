"""
Tool argument validation

Validates tool arguments against parameter schemas.
Extracted from BaseTool to follow Single Responsibility Principle.
"""

from typing import Dict, Any

from src.modules.xcp_server.tools.base.models import ToolDefinition
from src.modules.xcp_server.exceptions import XCPToolValidationError


class ArgumentValidator:
    """Validates tool arguments against schema definitions"""

    @staticmethod
    def validate(
        definition: ToolDefinition,
        arguments: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate arguments against tool schema

        Args:
            definition: Tool definition with parameter schema
            arguments: Raw arguments from MCP client

        Returns:
            Dict[str, Any]: Validated arguments with defaults applied

        Raises:
            XCPToolValidationError: If validation fails
        """
        validated = {}

        # Check required parameters and apply defaults
        for param in definition.parameters:
            if param.required and param.name not in arguments:
                raise XCPToolValidationError(
                    tool_name=definition.name,
                    message=f"Required parameter '{param.name}' is missing"
                )

            # Apply defaults
            if param.name not in arguments and param.default is not None:
                validated[param.name] = param.default
            elif param.name in arguments:
                validated[param.name] = arguments[param.name]

                # Validate enum
                if param.enum and validated[param.name] not in param.enum:
                    raise XCPToolValidationError(
                        tool_name=definition.name,
                        message=f"Parameter '{param.name}' must be one of {param.enum}"
                    )

        return validated

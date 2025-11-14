"""
XCPServer Custom Exceptions

Domain-specific exceptions for XCP server operations.
"""


class XCPServerError(Exception):
    """Base exception for all XCP server errors"""

    def __init__(self, message: str, code: str = "XCP_ERROR"):
        self.message = message
        self.code = code
        super().__init__(self.message)


class XCPServerNotEnabledError(XCPServerError):
    """Raised when attempting to use XCP server while it's disabled"""

    def __init__(self):
        super().__init__(
            "XCP server is not enabled. Set XCP_SERVER_ENABLED=true in environment.",
            code="XCP_NOT_ENABLED"
        )


class XCPToolError(XCPServerError):
    """Base exception for tool-related errors"""

    def __init__(self, tool_name: str, message: str):
        self.tool_name = tool_name
        super().__init__(
            f"Tool '{tool_name}' error: {message}",
            code="XCP_TOOL_ERROR"
        )


class XCPToolExecutionError(XCPToolError):
    """Raised when a tool fails during execution"""

    def __init__(self, tool_name: str, message: str, original_error: Exception = None):
        self.original_error = original_error
        super().__init__(tool_name, message)
        self.code = "XCP_TOOL_EXECUTION_ERROR"


class XCPToolValidationError(XCPToolError):
    """Raised when tool input validation fails"""

    def __init__(self, tool_name: str, message: str):
        super().__init__(tool_name, message)
        self.code = "XCP_TOOL_VALIDATION_ERROR"


class XCPProtocolError(XCPServerError):
    """Raised when MCP protocol errors occur"""

    def __init__(self, message: str):
        super().__init__(
            f"MCP protocol error: {message}",
            code="XCP_PROTOCOL_ERROR"
        )


class XCPTransportError(XCPServerError):
    """Raised when transport layer errors occur"""

    def __init__(self, transport_type: str, message: str):
        self.transport_type = transport_type
        super().__init__(
            f"Transport '{transport_type}' error: {message}",
            code="XCP_TRANSPORT_ERROR"
        )


class XCPResourceError(XCPServerError):
    """Raised when resource access errors occur"""

    def __init__(self, resource_uri: str, message: str):
        self.resource_uri = resource_uri
        super().__init__(
            f"Resource '{resource_uri}' error: {message}",
            code="XCP_RESOURCE_ERROR"
        )


class XCPConfigurationError(XCPServerError):
    """Raised when configuration errors occur"""

    def __init__(self, message: str):
        super().__init__(
            f"Configuration error: {message}",
            code="XCP_CONFIG_ERROR"
        )


class XCPDependencyError(XCPServerError):
    """Raised when required dependencies are missing or unavailable"""

    def __init__(self, dependency: str, message: str):
        self.dependency = dependency
        super().__init__(
            f"Dependency '{dependency}' error: {message}",
            code="XCP_DEPENDENCY_ERROR"
        )

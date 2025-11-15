"""XCPServer Service Layer

Main service: XCPServerService (facade that coordinates all sub-components)

Sub-components:
- registry: ToolFactory (creates tools), ToolRegistry (stores tools)
- lifecycle: ServerLifecycleManager (manages start/stop), InitializationCoordinator (initializes server)
- info: ServerInfoProvider (aggregates metadata)
"""

from .xcp_server_service import XCPServerService
from .registry import ToolFactory, ToolRegistry
from .lifecycle import ServerLifecycleManager, InitializationCoordinator, InitializationResult
from .info import ServerInfoProvider

__all__ = [
    # Main service
    "XCPServerService",
    # Registry components
    "ToolFactory",
    "ToolRegistry",
    # Lifecycle components
    "ServerLifecycleManager",
    "InitializationCoordinator",
    "InitializationResult",
    # Info components
    "ServerInfoProvider"
]

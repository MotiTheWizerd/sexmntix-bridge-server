"""
Base Tool Factory - Abstract base class for tool factories
"""
from abc import ABC, abstractmethod
from typing import List
from src.modules.xcp_server.tools import BaseTool


class BaseToolFactory(ABC):
    """
    Abstract base class for tool factories.

    All specialized tool factories should inherit from this class
    and implement the create_tools() method.
    """

    @abstractmethod
    def create_tools(self, **dependencies) -> List[BaseTool]:
        """
        Create and return a list of tools.

        Args:
            **dependencies: Various dependencies required by the tools

        Returns:
            List of initialized BaseTool instances
        """
        pass

    def _validate_dependency(self, dependency, name: str):
        """
        Validate that a required dependency is not None.

        Args:
            dependency: The dependency to validate
            name: Name of the dependency for error messages

        Raises:
            ValueError: If the dependency is None
        """
        if dependency is None:
            raise ValueError(f"Required dependency '{name}' cannot be None")

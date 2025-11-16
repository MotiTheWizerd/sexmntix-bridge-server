"""
Service Container for Dependency Injection

Manages service lifecycle, dependency resolution, and scoping.
"""

from typing import Type, TypeVar, Callable, Dict, Any, Optional, List
from enum import Enum
import inspect
from src.modules.core import EventBus, Logger

T = TypeVar('T')


class ServiceScope(str, Enum):
    """Service lifecycle scopes"""
    SINGLETON = "singleton"  # One instance for app lifetime
    TRANSIENT = "transient"  # New instance per request
    SCOPED = "scoped"        # One instance per scope (e.g., per-project)


class ServiceContainer:
    """
    Centralized dependency injection container.

    Manages service registration, instantiation, and lifecycle.
    Automatically resolves dependencies via constructor injection.
    """

    def __init__(self):
        self._singletons: Dict[Type, Any] = {}
        self._factories: Dict[Type, Callable] = {}
        self._scopes: Dict[Type, ServiceScope] = {}
        self._initialized: bool = False
        self.logger: Optional[Logger] = None

    def register_singleton(self, service_type: Type[T], instance: T) -> None:
        """
        Register a singleton service instance.

        Args:
            service_type: The type/interface of the service
            instance: The service instance
        """
        self._singletons[service_type] = instance
        self._scopes[service_type] = ServiceScope.SINGLETON

    def register_factory(
        self,
        service_type: Type[T],
        factory: Callable[..., T],
        scope: ServiceScope = ServiceScope.SINGLETON
    ) -> None:
        """
        Register a service factory function.

        Args:
            service_type: The type/interface of the service
            factory: Factory function that creates the service
            scope: Service lifecycle scope
        """
        self._factories[service_type] = factory
        self._scopes[service_type] = scope

    def register_class(
        self,
        service_type: Type[T],
        implementation: Optional[Type[T]] = None,
        scope: ServiceScope = ServiceScope.SINGLETON
    ) -> None:
        """
        Register a class for auto-instantiation with dependency injection.

        Args:
            service_type: The type/interface of the service
            implementation: The implementation class (defaults to service_type)
            scope: Service lifecycle scope
        """
        impl = implementation or service_type

        def factory() -> T:
            # Get constructor parameters
            sig = inspect.signature(impl.__init__)
            params = {}

            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue

                # Try to resolve dependency by type annotation
                if param.annotation != inspect.Parameter.empty:
                    param_type = param.annotation
                    if self.has(param_type):
                        params[param_name] = self.get(param_type)

            return impl(**params)

        self.register_factory(service_type, factory, scope)

    def get(self, service_type: Type[T]) -> T:
        """
        Get a service instance (with automatic dependency resolution).

        Args:
            service_type: The type of service to retrieve

        Returns:
            Service instance

        Raises:
            KeyError: If service not registered
        """
        # Check if singleton already exists
        if service_type in self._singletons:
            return self._singletons[service_type]

        # Check if factory exists
        if service_type not in self._factories:
            raise KeyError(f"Service {service_type.__name__} not registered")

        # Get scope
        scope = self._scopes.get(service_type, ServiceScope.TRANSIENT)

        # Create instance
        factory = self._factories[service_type]
        instance = factory()

        # Store singleton
        if scope == ServiceScope.SINGLETON:
            self._singletons[service_type] = instance

        return instance

    def has(self, service_type: Type[T]) -> bool:
        """
        Check if a service is registered.

        Args:
            service_type: The type to check

        Returns:
            True if registered, False otherwise
        """
        return service_type in self._singletons or service_type in self._factories

    def get_all(self) -> Dict[Type, Any]:
        """
        Get all registered singleton services.

        Returns:
            Dictionary of service type to instance
        """
        return dict(self._singletons)

    async def initialize_all(self) -> None:
        """
        Initialize all registered services.

        Creates singleton instances and calls any initialization methods.
        """
        if self._initialized:
            return

        if self.logger:
            self.logger.info("Initializing all services in DI container...")

        # Initialize all singletons
        for service_type in self._factories.keys():
            if self._scopes.get(service_type) == ServiceScope.SINGLETON:
                if service_type not in self._singletons:
                    self.get(service_type)

        self._initialized = True

        if self.logger:
            self.logger.info(f"DI container initialized with {len(self._singletons)} services")

    async def shutdown_all(self) -> None:
        """
        Shutdown all services gracefully.

        Calls close() or shutdown() methods if they exist.
        """
        if self.logger:
            self.logger.info("Shutting down all services in DI container...")

        for service_type, instance in self._singletons.items():
            try:
                # Try calling close() method
                if hasattr(instance, 'close'):
                    close_method = getattr(instance, 'close')
                    if inspect.iscoroutinefunction(close_method):
                        await close_method()
                    else:
                        close_method()

                # Try calling shutdown() method
                elif hasattr(instance, 'shutdown'):
                    shutdown_method = getattr(instance, 'shutdown')
                    if inspect.iscoroutinefunction(shutdown_method):
                        await shutdown_method()
                    else:
                        shutdown_method()
            except Exception as e:
                if self.logger:
                    self.logger.error(
                        f"Error shutting down {service_type.__name__}: {e}",
                        exc_info=True
                    )

        self._initialized = False

        if self.logger:
            self.logger.info("All services shut down")

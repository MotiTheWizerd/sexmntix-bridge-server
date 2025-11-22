from fastapi import FastAPI
from dotenv import load_dotenv

from src.api.bootstrap.config import load_app_config, load_service_config
from src.api.bootstrap.services import initialize_core_services, initialize_embedding_service
from src.api.bootstrap.lifecycle import LifecycleOrchestrator
from src.api.bootstrap.middleware import MiddlewareConfigurator
from src.api.bootstrap.router_registry import RouterRegistry

load_dotenv()

# Load configuration
app_config = load_app_config()
service_config = load_service_config()

# Initialize core services that need to be available before app creation
event_bus, logger, socket_service = initialize_core_services()

# Initialize embedding service
embedding_service = initialize_embedding_service(service_config, event_bus, logger)


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.

    Uses orchestrator pattern to delegate responsibilities:
    - LifecycleOrchestrator: Manages startup/shutdown sequences
    - MiddlewareConfigurator: Configures middleware and exception handlers
    - RouterRegistry: Registers all routes and Socket.IO

    Returns:
        Configured FastAPI application instance
    """
    # Create lifecycle orchestrator
    lifecycle_orchestrator = LifecycleOrchestrator(
        app_config=app_config,
        service_config=service_config,
        event_bus=event_bus,
        logger=logger,
        socket_service=socket_service,
        embedding_service=embedding_service
    )

    # Create FastAPI app with lifecycle management
    app = FastAPI(
        title=app_config.title,
        description=app_config.description,
        version=app_config.version,
        lifespan=lifecycle_orchestrator.lifespan
    )

    # Configure middleware and exception handlers
    MiddlewareConfigurator.configure(app, app_config, logger)

    # Register all routes and Socket.IO
    RouterRegistry.register_all(app, socket_service, embedding_service)

    return app

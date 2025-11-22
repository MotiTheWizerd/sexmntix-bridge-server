"""
Middleware configuration for FastAPI application.

Handles CORS, logging middleware, and custom exception handlers.
"""

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from src.api.middleware.logging import LoggingMiddleware
from src.api.bootstrap.config import AppConfig
from src.modules.core import Logger


class MiddlewareConfigurator:
    """Configures middleware and exception handlers for FastAPI app."""

    @staticmethod
    def configure(app: FastAPI, app_config: AppConfig, logger: Logger):
        """
        Configure all middleware and exception handlers.

        Args:
            app: FastAPI application instance
            app_config: Application configuration
            logger: Logger instance for error logging
        """
        MiddlewareConfigurator._add_exception_handlers(app, logger)
        MiddlewareConfigurator._add_cors_middleware(app, app_config)
        MiddlewareConfigurator._add_logging_middleware(app)

    @staticmethod
    def _add_exception_handlers(app: FastAPI, logger: Logger):
        """Add custom exception handlers to the app."""

        @app.exception_handler(RequestValidationError)
        async def validation_exception_handler(request: Request, exc: RequestValidationError):
            # Log detailed validation errors
            logger.error(f"Validation error on {request.method} {request.url.path}")
            logger.error(f"Validation errors: {exc.errors()}")

            # Try to get request body for debugging
            try:
                body = await request.body()
                logger.error(f"Request body: {body.decode('utf-8')}")
            except Exception as e:
                logger.error(f"Could not read request body: {e}")

            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content={
                    "detail": exc.errors(),
                    "body": str(exc.body) if hasattr(exc, 'body') else None
                }
            )

    @staticmethod
    def _add_cors_middleware(app: FastAPI, app_config: AppConfig):
        """Add CORS middleware to the app."""
        app.add_middleware(
            CORSMiddleware,
            allow_origins=app_config.cors_allow_origins,
            allow_credentials=app_config.cors_allow_credentials,
            allow_methods=app_config.cors_allow_methods,
            allow_headers=app_config.cors_allow_headers,
        )

    @staticmethod
    def _add_logging_middleware(app: FastAPI):
        """Add logging middleware to the app."""
        app.add_middleware(LoggingMiddleware)

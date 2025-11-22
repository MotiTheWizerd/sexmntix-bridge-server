"""
Router registration for FastAPI application.

Centralizes all route and Socket.IO mounting logic.
"""

from fastapi import FastAPI
from typing import Optional
import socketio
from src.api.routes import (
    health,
    memory_logs,
    mental_notes,
    users,
    socket_test,
    memory_logs_example,
    embeddings,
    monitoring,
    conversations,
    user_projects
)
from src.services.socket_service import SocketService


class RouterRegistry:
    """Manages registration of all application routes and Socket.IO."""

    @staticmethod
    def register_all(app: FastAPI, socket_service: SocketService, embedding_service: Optional[object] = None):
        """
        Register all routes and mount Socket.IO.

        Args:
            app: FastAPI application instance
            socket_service: SocketService instance for Socket.IO
            embedding_service: Optional embedding service (embeddings routes only registered if available)
        """
        RouterRegistry._register_core_routes(app)
        RouterRegistry._register_optional_routes(app, embedding_service)
        RouterRegistry._mount_socketio(app, socket_service)

    @staticmethod
    def _register_core_routes(app: FastAPI):
        """Register core routes that are always available."""
        app.include_router(health.router)
        app.include_router(memory_logs.router)
        app.include_router(mental_notes.router)
        app.include_router(conversations.router)
        app.include_router(users.router)
        app.include_router(socket_test.router)
        app.include_router(memory_logs_example.router)
        app.include_router(monitoring.router)
        app.include_router(user_projects.router)

    @staticmethod
    def _register_optional_routes(app: FastAPI, embedding_service: Optional[object]):
        """Register optional routes based on service availability."""
        # Register embeddings router if service is available
        if embedding_service:
            app.include_router(embeddings.router)

    @staticmethod
    def _mount_socketio(app: FastAPI, socket_service: SocketService):
        """Mount Socket.IO ASGI app."""
        socket_app = socketio.ASGIApp(socket_service.sio, other_asgi_app=None)
        app.mount("/socket.io", socket_app)

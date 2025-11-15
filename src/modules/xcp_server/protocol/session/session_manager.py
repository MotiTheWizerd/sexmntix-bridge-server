"""
Session Manager

Manages active MCP client sessions and provides session tracking capabilities.
"""

from typing import Dict, Any, Optional
from src.modules.core import Logger


class SessionManager:
    """Manages active MCP client sessions

    This class tracks active client sessions and provides methods for
    session lifecycle management including creation, tracking, and cleanup.
    """

    def __init__(self, logger: Logger):
        """Initialize session manager

        Args:
            logger: Logger instance for session tracking
        """
        self.logger = logger
        self.active_sessions: Dict[str, Any] = {}

    def create_session(self, session_id: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Create a new session

        Args:
            session_id: Unique session identifier
            metadata: Optional metadata to associate with the session
        """
        self.active_sessions[session_id] = metadata or {}
        self.logger.debug(
            f"Created session: {session_id}",
            extra={"session_id": session_id}
        )

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session metadata by ID

        Args:
            session_id: Session identifier

        Returns:
            Session metadata if found, None otherwise
        """
        return self.active_sessions.get(session_id)

    def update_session(self, session_id: str, metadata: Dict[str, Any]) -> None:
        """Update session metadata

        Args:
            session_id: Session identifier
            metadata: New metadata to merge with existing
        """
        if session_id in self.active_sessions:
            self.active_sessions[session_id].update(metadata)
            self.logger.debug(
                f"Updated session: {session_id}",
                extra={"session_id": session_id}
            )

    def remove_session(self, session_id: str) -> None:
        """Remove a session

        Args:
            session_id: Session identifier
        """
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
            self.logger.debug(
                f"Removed session: {session_id}",
                extra={"session_id": session_id}
            )

    def clear_all_sessions(self) -> None:
        """Clear all active sessions

        This is typically called during server shutdown to cleanup
        any remaining session state.
        """
        session_count = len(self.active_sessions)
        self.active_sessions.clear()
        self.logger.info(f"Cleared {session_count} active sessions")

    def get_session_count(self) -> int:
        """Get the number of active sessions

        Returns:
            Number of active sessions
        """
        return len(self.active_sessions)

    def list_session_ids(self) -> list[str]:
        """List all active session IDs

        Returns:
            List of active session identifiers
        """
        return list(self.active_sessions.keys())

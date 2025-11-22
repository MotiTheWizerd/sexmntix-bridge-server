"""
Logging message formatters for internal handlers.

Provides consistent log message formatting across
memory log and mental note storage handlers.
"""

from typing import Dict, Any, List
from .config import InternalHandlerConfig


class LogMessageFormatter:
    """Formats log messages for event handlers"""

    @staticmethod
    def format_event_received(prefix: str, event_data: Dict[str, Any]) -> str:
        """
        Format event received message.

        Args:
            prefix: Log prefix (e.g., [EVENT_HANDLER])
            event_data: Event payload

        Returns:
            Formatted log message
        """
        keys = list(event_data.keys())
        return f"{prefix} Received event with keys: {keys}"

    @staticmethod
    def format_processing_started(
        prefix: str,
        doc_id: int,
        user_id: str,
        project_id: str,
        doc_type: str = "memory_log"
    ) -> str:
        """
        Format processing started message.

        Args:
            prefix: Log prefix
            doc_id: Document ID (memory_log_id or mental_note_id)
            user_id: User identifier
            project_id: Project identifier
            doc_type: Type of document ("memory_log" or "mental_note")

        Returns:
            Formatted log message
        """
        return (
            f"{prefix} Processing {doc_type}_id={doc_id}, "
            f"user_id={user_id}, project_id={project_id}"
        )

    @staticmethod
    def format_generating_vector(
        prefix: str,
        doc_id: int,
        user_id: str,
        project_id: str,
        doc_type: str = "memory_log"
    ) -> str:
        """
        Format generating vector message.

        Args:
            prefix: Log prefix
            doc_id: Document ID
            user_id: User identifier
            project_id: Project identifier
            doc_type: Type of document

        Returns:
            Formatted log message
        """
        return (
            f"{prefix} Generating and storing vector for {doc_type} {doc_id} "
            f"(user: {user_id}, project: {project_id})"
        )

    @staticmethod
    def format_memory_log_keys(prefix: str, keys: List[str]) -> str:
        """
        Format memory log keys message.

        Args:
            prefix: Log prefix
            keys: List of memory_log dictionary keys

        Returns:
            Formatted log message
        """
        return f"{prefix} memory_log keys: {keys}"

    @staticmethod
    def format_content_info(
        prefix: str,
        exists: bool,
        content_type: str,
        length: int
    ) -> str:
        """
        Format content info message.

        Args:
            prefix: Log prefix
            exists: Whether content exists
            content_type: Type name of content
            length: Length of content

        Returns:
            Formatted log message
        """
        return (
            f"{prefix} content field - exists: {exists}, "
            f"type: {content_type}, length: {length}"
        )

    @staticmethod
    def format_content_preview(prefix: str, preview: str) -> str:
        """
        Format content preview message.

        Args:
            prefix: Log prefix
            preview: Content preview string

        Returns:
            Formatted log message
        """
        return f"{prefix} content preview: {preview}"

    @staticmethod
    def format_calling_store(prefix: str, method_name: str) -> str:
        """
        Format calling store method message.

        Args:
            prefix: Log prefix
            method_name: Name of storage method being called

        Returns:
            Formatted log message
        """
        return f"{prefix} Calling {method_name}..."

    @staticmethod
    def format_vector_stored(
        prefix: str,
        vector_id: str,
        doc_id: int,
        doc_type: str = "memory_log"
    ) -> str:
        """
        Format vector stored success message.

        Args:
            prefix: Log prefix
            vector_id: Vector storage ID
            doc_id: Document ID
            doc_type: Type of document

        Returns:
            Formatted log message
        """
        return f"{prefix} Vector stored with {doc_type}_id: {vector_id} for {doc_type} {doc_id}"

    @staticmethod
    def format_mental_note_stored(
        prefix: str,
        note_id: str,
        embedding_dim: int
    ) -> str:
        """
        Format mental note vector stored message (with embedding dimensions).

        Args:
            prefix: Log prefix
            note_id: Note ID from ChromaDB
            embedding_dim: Embedding vector dimensions

        Returns:
            Formatted log message
        """
        return (
            f"{prefix} Mental note vector stored with id: {note_id}, "
            f"embedding dimensions: {embedding_dim}"
        )

    @staticmethod
    def format_postgres_updated(prefix: str, doc_id: int, doc_type: str = "memory_log") -> str:
        """
        Format PostgreSQL update success message.

        Args:
            prefix: Log prefix
            doc_id: Document ID
            doc_type: Type of document

        Returns:
            Formatted log message
        """
        return f"PostgreSQL updated for {doc_type} {doc_id}"

    @staticmethod
    def format_postgres_error(
        prefix: str,
        doc_id: int,
        error: Exception,
        doc_type: str = "memory_log"
    ) -> str:
        """
        Format PostgreSQL update error message.

        Args:
            prefix: Log prefix
            doc_id: Document ID
            error: Exception that occurred
            doc_type: Type of document

        Returns:
            Formatted log message
        """
        return (
            f"PostgreSQL update failed for {doc_type} {doc_id}: {error}. "
            f"Vector storage in ChromaDB succeeded."
        )

    @staticmethod
    def format_validation_error(prefix: str, reason: str) -> str:
        """
        Format validation error message.

        Args:
            prefix: Log prefix
            reason: Reason for validation failure

        Returns:
            Formatted log message
        """
        return f"Skipping vector storage: {reason}"

    @staticmethod
    def format_handler_error(doc_id: Any, error: Exception, doc_type: str = "memory_log") -> str:
        """
        Format handler error message.

        Args:
            doc_id: Document ID
            error: Exception that occurred
            doc_type: Type of document

        Returns:
            Formatted log message
        """
        return f"Failed to store vector for {doc_type} {doc_id}: {error}"

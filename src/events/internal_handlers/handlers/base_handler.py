"""
Base handler for storage events.

Provides shared logic and template method pattern for
memory log and mental note storage handlers.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Tuple, List, Callable
from src.modules.core import EventBus, Logger
from src.modules.embeddings import EmbeddingService
from ..config import InternalHandlerConfig
from ..validators import EventDataValidator
from ..formatters import LogMessageFormatter
from ..orchestrators import VectorStorageOrchestrator
from ..utils.db_updater import DatabaseEmbeddingUpdater


class BaseStorageHandler(ABC):
    """Base class for storage event handlers using template method pattern"""

    def __init__(
        self,
        db_session_factory: Callable,
        embedding_service: EmbeddingService,
        event_bus: EventBus,
        logger: Logger
    ):
        """
        Initialize base handler with all dependencies.

        Args:
            db_session_factory: Callable returning AsyncSession for PostgreSQL
            embedding_service: Service for generating embeddings
            event_bus: Event bus for publishing events
            logger: Logger instance
        """
        self.db_session_factory = db_session_factory
        self.embedding_service = embedding_service
        self.event_bus = event_bus
        self.logger = logger

        # Initialize composed components
        self.validator = EventDataValidator()
        self.formatter = LogMessageFormatter()
        self.orchestrator = VectorStorageOrchestrator(
            embedding_service, event_bus, logger
        )
        self.db_updater = DatabaseEmbeddingUpdater(
            db_session_factory, logger
        )

    async def handle_stored_event(self, event_data: Dict[str, Any]):
        """
        Template method for handling stored events.

        This method defines the skeleton of the algorithm,
        delegating specific steps to abstract methods.

        Args:
            event_data: Event payload containing document data and ID
        """
        try:
            # Step 1: Log event reception
            self._log_event_received(event_data)

            # Step 2: Extract and validate
            validated = self._extract_and_validate(event_data)
            if not validated:
                return

            # Step 3: Log processing details
            self._log_processing_details(validated)

            # Step 4: Store vector in ChromaDB
            vector_id, embedding = await self._store_vector(validated)

            # Step 5: Log vector storage success
            self._log_vector_stored(vector_id, validated, embedding)

            # Step 6: Update PostgreSQL with embedding
            await self._update_database(validated, embedding)

        except Exception as e:
            self._handle_error(e, event_data)

    @abstractmethod
    def _get_log_prefix(self) -> str:
        """Get log prefix for this handler (implemented by subclasses)"""
        pass

    @abstractmethod
    def _get_doc_type(self) -> str:
        """Get document type name (implemented by subclasses)"""
        pass

    @abstractmethod
    def _extract_and_validate(self, event_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract and validate event data (implemented by subclasses)"""
        pass

    @abstractmethod
    async def _store_vector(self, validated: Dict[str, Any]) -> Tuple[str, List[float]]:
        """Store vector in ChromaDB (implemented by subclasses)"""
        pass

    @abstractmethod
    async def _update_database(self, validated: Dict[str, Any], embedding: List[float]):
        """Update PostgreSQL with embedding (implemented by subclasses)"""
        pass

    def _log_event_received(self, event_data: Dict[str, Any]):
        """Log event reception"""
        message = self.formatter.format_event_received(
            self._get_log_prefix(),
            event_data
        )
        self.logger.info(message)

    def _log_processing_details(self, validated: Dict[str, Any]):
        """Log processing details including content analysis"""
        prefix = self._get_log_prefix()
        memory_log = validated.get("memory_log") or validated.get("content", {})
        doc_id = self._get_doc_id(validated)

        # Log processing started
        message = self.formatter.format_processing_started(
            prefix,
            doc_id,
            validated["user_id"],
            validated["project_id"],
            self._get_doc_type()
        )
        self.logger.info(message)

        # Log generating vector
        message = self.formatter.format_generating_vector(
            prefix,
            doc_id,
            validated["user_id"],
            validated["project_id"],
            self._get_doc_type()
        )
        self.logger.info(message)

        # Log memory_log keys
        if isinstance(memory_log, dict):
            message = self.formatter.format_memory_log_keys(prefix, list(memory_log.keys()))
            self.logger.info(message)

            # Log content info
            content_info = self.validator.get_content_info(memory_log)
            message = self.formatter.format_content_info(
                prefix,
                content_info["exists"],
                content_info["type"],
                content_info["length"]
            )
            self.logger.info(message)

            # Log content preview
            preview = self.validator.extract_content_preview(memory_log)
            message = self.formatter.format_content_preview(prefix, preview)
            self.logger.info(message)

    def _log_vector_stored(
        self,
        vector_id: str,
        validated: Dict[str, Any],
        embedding: List[float]
    ):
        """Log vector storage success (can be overridden for custom formatting)"""
        doc_id = self._get_doc_id(validated)
        message = self.formatter.format_vector_stored(
            self._get_log_prefix(),
            vector_id,
            doc_id,
            self._get_doc_type()
        )
        self.logger.info(message)

    def _handle_error(self, error: Exception, event_data: Dict[str, Any]):
        """Handle errors during event processing"""
        doc_id = event_data.get(self._get_doc_id_field())
        message = self.formatter.format_handler_error(
            doc_id,
            error,
            self._get_doc_type()
        )
        self.logger.error(message)
        # Non-blocking failure - document already exists in PostgreSQL

    @abstractmethod
    def _get_doc_id(self, validated: Dict[str, Any]) -> int:
        """Get document ID from validated data (implemented by subclasses)"""
        pass

    @abstractmethod
    def _get_doc_id_field(self) -> str:
        """Get document ID field name (implemented by subclasses)"""
        pass

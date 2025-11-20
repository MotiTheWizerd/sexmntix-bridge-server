"""
Conversation database model.

Stores AI conversation data with vector embeddings for semantic search.
"""

from sqlalchemy import String, Integer, DateTime
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional
import uuid
from .base import Base


class Conversation(Base):
    """
    Conversation model for storing AI conversations.

    Vector embeddings are stored ONLY in ChromaDB (conversations_{hash} collection),
    NOT in PostgreSQL. This avoids pgvector dependency while maintaining full
    semantic search capabilities.

    Attributes:
        id: Primary key (UUID)
        conversation_id: Unique conversation identifier (UUID from client)
        model: AI model used (e.g., "gpt-5-1-instant")
        raw_data: Complete conversation data (JSONB)
        user_id: User identifier for multi-tenant isolation
        project_id: Project identifier for multi-tenant isolation
        session_id: Session identifier for grouping related conversations
        created_at: Timestamp of creation
    """

    __tablename__ = "conversations"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Conversation identifier from client (allows duplicates for versioning)
    conversation_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)

    # AI model used
    model: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Complete conversation data (messages array, metadata)
    raw_data: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Multi-tenant isolation
    user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    project_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

    # Session grouping
    session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, conversation_id={self.conversation_id}, model={self.model})>"

"""
Conversation database model.

Stores AI conversation data with vector embeddings for semantic search.
"""

from sqlalchemy import String, Integer, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional
from pgvector.sqlalchemy import Vector
from .base import Base


class Conversation(Base):
    """
    Conversation model for storing AI conversations.

    Stores complete conversation history with embeddings in both PostgreSQL
    and ChromaDB (separate collection: conversations_{hash}).

    Attributes:
        id: Primary key
        conversation_id: Unique conversation identifier (UUID from client)
        model: AI model used (e.g., "gpt-5-1-instant")
        raw_data: Complete conversation data (JSONB)
        embedding: Vector embedding for semantic search (768 dimensions)
        user_id: User identifier for multi-tenant isolation
        project_id: Project identifier for multi-tenant isolation
        created_at: Timestamp of creation
    """

    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Unique conversation identifier from client
    conversation_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    # AI model used
    model: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    # Complete conversation data (messages array, metadata)
    raw_data: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Vector embedding for semantic search (768 dimensions for Google text-embedding-004)
    embedding: Mapped[Optional[list]] = mapped_column(Vector(768), nullable=True)

    # Multi-tenant isolation
    user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    project_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<Conversation(id={self.id}, conversation_id={self.conversation_id}, model={self.model})>"

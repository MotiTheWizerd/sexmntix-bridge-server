from sqlalchemy import String, Integer, DateTime, Float
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, UUID, TSVECTOR
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional, Any
import uuid
from pgvector.sqlalchemy import Vector
from .base import Base


class MemoryLog(Base):
    __tablename__ = "memory_logs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    task: Mapped[str] = mapped_column(String(255), index=True)
    agent: Mapped[str] = mapped_column(String(100), index=True)

    # Session ID for grouping related memories
    session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

    # Memory log data (flattened from raw_data wrapper)
    memory_log: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Document type for unified semantic space
    document_type: Mapped[str] = mapped_column(String(50), default="memory_log", index=True)

    # Vector embedding for semantic search (768 dimensions)
    # Using pgvector's Vector type for efficient similarity search
    embedding: Mapped[Optional[list]] = mapped_column(Vector(768), nullable=True)

    # User and project isolation for ChromaDB collections
    user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    project_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

    # Full-text search vector for hybrid search (auto-updated by trigger)
    search_vector: Mapped[Optional[Any]] = mapped_column(TSVECTOR, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

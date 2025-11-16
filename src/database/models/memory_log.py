from sqlalchemy import String, Integer, DateTime, Float
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional
from pgvector.sqlalchemy import Vector
from .base import Base


class MemoryLog(Base):
    __tablename__ = "memory_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task: Mapped[str] = mapped_column(String(255), index=True)
    agent: Mapped[str] = mapped_column(String(100), index=True)
    date: Mapped[datetime] = mapped_column(DateTime, index=True)
    raw_data: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Document type for unified semantic space
    document_type: Mapped[str] = mapped_column(String(50), default="memory_log", index=True)

    # Vector embedding for semantic search (768 dimensions)
    # Using pgvector's Vector type for efficient similarity search
    embedding: Mapped[Optional[list]] = mapped_column(Vector(768), nullable=True)

    # User and project isolation for ChromaDB collections
    user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    project_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

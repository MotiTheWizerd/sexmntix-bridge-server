from sqlalchemy import String, Integer, DateTime, BigInteger, Float, Text
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional
import uuid
from pgvector.sqlalchemy import Vector
from .base import Base


class MentalNote(Base):
    __tablename__ = "mental_notes"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    note_type: Mapped[str] = mapped_column(String(50), default="note", index=True)
    meta_data: Mapped[dict] = mapped_column(JSONB, default=dict, server_default='{}')

    # Vector embedding for semantic search (1536 dimensions)
    # Using pgvector's Vector type for efficient similarity search
    embedding: Mapped[Optional[list]] = mapped_column(Vector(1536), nullable=True)

    # User and project isolation for ChromaDB collections
    user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    project_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

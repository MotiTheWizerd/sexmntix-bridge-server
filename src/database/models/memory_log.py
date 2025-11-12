from sqlalchemy import String, Integer, DateTime, Float
from sqlalchemy.dialects.postgresql import JSONB, ARRAY
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional
from .base import Base


class MemoryLog(Base):
    __tablename__ = "memory_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task: Mapped[str] = mapped_column(String(255), index=True)
    agent: Mapped[str] = mapped_column(String(100), index=True)
    date: Mapped[datetime] = mapped_column(DateTime, index=True)
    raw_data: Mapped[dict] = mapped_column(JSONB, nullable=False)

    # Vector embedding for semantic search (768 dimensions)
    embedding: Mapped[Optional[list]] = mapped_column(ARRAY(Float), nullable=True)

    # User and project isolation for ChromaDB collections
    user_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    project_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

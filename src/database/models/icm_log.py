from datetime import datetime
import uuid
from typing import Optional, Any

from sqlalchemy import String, DateTime, Integer, Float, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class IcmLog(Base):
    __tablename__ = "icm_logs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    icm_type: Mapped[str] = mapped_column(String(32), index=True)
    query: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    project_id: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    retrieval_strategy: Mapped[Optional[str]] = mapped_column(String(64), nullable=True)
    required_memory: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    time_window_start: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    time_window_end: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    payload: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    results_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    limit: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    min_similarity: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

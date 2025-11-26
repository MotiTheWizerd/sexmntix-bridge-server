from datetime import datetime
import uuid
from typing import Optional, Any

from sqlalchemy import String, DateTime, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class RequestLog(Base):
    __tablename__ = "request_logs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    request_id: Mapped[Optional[str]] = mapped_column(String(64), index=True, nullable=True)
    path: Mapped[Optional[str]] = mapped_column(String(512), index=True, nullable=True)
    method: Mapped[Optional[str]] = mapped_column(String(16), index=True, nullable=True)
    user_id: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    project_id: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    session_id: Mapped[Optional[str]] = mapped_column(String(255), index=True, nullable=True)
    query_params: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    headers: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    body: Mapped[Optional[Any]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)

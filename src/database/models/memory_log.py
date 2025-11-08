from sqlalchemy import String, Integer, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from .base import Base


class MemoryLog(Base):
    __tablename__ = "memory_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    task: Mapped[str] = mapped_column(String(255), index=True)
    agent: Mapped[str] = mapped_column(String(100), index=True)
    date: Mapped[datetime] = mapped_column(DateTime, index=True)
    raw_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

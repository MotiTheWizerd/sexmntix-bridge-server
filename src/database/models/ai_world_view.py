"""
AI World View database model.

Stores core beliefs and identity summaries for AI assistants per user/project.
"""

from sqlalchemy import String, Text, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from typing import Optional
import uuid
from .base import Base


class AIWorldView(Base):
    """
    AI World View model for storing core beliefs and identity.

    Attributes:
        id: Primary key (UUID)
        user_id: User identifier (UUID)
        project_id: Project identifier (UUID)
        core_beliefs: Summary of core beliefs about identity
        created_at: Timestamp of creation
        updated_at: Timestamp of last update
    """

    __tablename__ = "ai_world_views"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))

    # Multi-tenant isolation
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False, index=True)
    project_id: Mapped[str] = mapped_column(UUID(as_uuid=False), nullable=False, index=True)

    # Core beliefs summary
    core_beliefs: Mapped[str] = mapped_column(Text, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    def __repr__(self) -> str:
        return f"<AIWorldView(id={self.id}, user_id={self.user_id}, project_id={self.project_id})>"

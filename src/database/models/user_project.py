from sqlalchemy import String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from datetime import datetime
import uuid
from .base import Base
from .enums import ProjectType

class UserProject(Base):
    __tablename__ = "user_projects"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    project_name: Mapped[str] = mapped_column(String(255), nullable=True)
    project_type: Mapped[ProjectType] = mapped_column(Enum(ProjectType, name="projecttype"), nullable=False, default=ProjectType.VSCODE)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

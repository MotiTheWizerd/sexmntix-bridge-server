from sqlalchemy import String, DateTime, Text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from datetime import datetime
import uuid
from .base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    first_name: Mapped[str] = mapped_column(String(255), nullable=False)
    last_name: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    
    # === Model Configuration ===
    # Background workers configuration (flexible JSON for N agents)
    # Current workers:
    #   - conversation_analyzer: Converts AI responses into memory units (SXThalamus)
    #   - memory_synthesizer: Synthesizes retrieved memories into natural language context
    # Future workers: emotion_analyzer, fact_checker, pattern_recognizer, etc.
    background_workers: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
        default=lambda: {
            "conversation_analyzer": {
                "provider": "google",
                "model": "gemini-2.0-flash",
                "enabled": True
            },
            "memory_synthesizer": {
                "provider": "google",
                "model": "gemini-2.0-flash",
                "enabled": True
            }
        },
        server_default='{"conversation_analyzer": {"provider": "google", "model": "gemini-2.0-flash", "enabled": true}, "memory_synthesizer": {"provider": "google", "model": "gemini-2.0-flash", "enabled": true}}'
    )
    
    # Embedding model for vector storage
    embedding_model: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default="models/gemini-embedding-001",
        server_default="models/gemini-embedding-001"
    )

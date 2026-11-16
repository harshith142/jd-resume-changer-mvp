import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Boolean, Enum as SQLEnum, ForeignKey, Index, LargeBinary
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from app.database import Base
from app.models.user import GUID
import enum


class LLMProvider(str, enum.Enum):
    GEMINI = 'gemini'
    OPENAI = 'openai'
    ANTHROPIC = 'anthropic'
    GROK = 'grok'
    OPENROUTER = 'openrouter'
    NVIDIA = 'nvidia'
    OLLAMA = 'ollama'


class APIKey(Base):
    __tablename__ = 'api_keys'

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey('users.id', ondelete='CASCADE'),
        index=True,
        nullable=False,
    )
    provider: Mapped[LLMProvider] = mapped_column(
        SQLEnum(LLMProvider, native_enum=False),
        nullable=False,
    )
    # Encrypted key (AES-256-GCM) - LargeBinary works across PostgreSQL and SQLite
    key_encrypted: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    key_nonce: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    # Model configuration
    model: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    ollama_host: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    # Session-only flag (if True, key never persisted, sent per-request)
    is_session_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    # Last tested timestamp
    last_tested_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    # Last test result (True if last test passed)
    is_valid: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationship
    user: Mapped['User'] = relationship('User', back_populates='api_keys', lazy='selectin')

    __table_args__ = (
        Index('ix_api_keys_user_provider', 'user_id', 'provider', unique=True),
    )

    def __repr__(self) -> str:
        return f'<APIKey(id={self.id}, user_id={self.user_id}, provider={self.provider}, session_only={self.is_session_only})>'

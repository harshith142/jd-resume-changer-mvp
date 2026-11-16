import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Boolean, Enum as SQLEnum, UniqueConstraint, Index, LargeBinary, func, TypeDecorator, CHAR
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional

from app.database import Base
import enum


class OAuthProvider(str, enum.Enum):
    GOOGLE = 'google'
    GITHUB = 'github'


# Cross-platform UUID type that works with both PostgreSQL and SQLite
class GUID(TypeDecorator):
    '''Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(36) storing as string.
    '''
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            return dialect.type_descriptor(PGUUID())
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if isinstance(value, uuid.UUID):
                return str(value)
            return value

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == 'postgresql':
            return value
        else:
            if isinstance(value, str):
                return uuid.UUID(value)
            return value


class User(Base):
    __tablename__ = 'users'

    id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    avatar_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    oauth_provider: Mapped[Optional[OAuthProvider]] = mapped_column(
        SQLEnum(OAuthProvider, native_enum=False),
        nullable=True,
    )
    oauth_subject: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True, nullable=True)
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
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    refresh_token_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    # Relationships
    api_keys: Mapped[list['APIKey']] = relationship(
        'APIKey',
        back_populates='user',
        cascade='all, delete-orphan',
        lazy='selectin',
    )
    master_resumes: Mapped[list['MasterResume']] = relationship(
        'MasterResume',
        back_populates='user',
        cascade='all, delete-orphan',
        lazy='selectin',
    )
    job_descriptions: Mapped[list['JobDescription']] = relationship(
        'JobDescription',
        back_populates='user',
        cascade='all, delete-orphan',
        lazy='selectin',
    )
    generated_resumes: Mapped[list['GeneratedResume']] = relationship(
        'GeneratedResume',
        back_populates='user',
        cascade='all, delete-orphan',
        lazy='selectin',
    )

    __table_args__ = (
        Index('ix_users_oauth_provider_subject', 'oauth_provider', 'oauth_subject'),
    )

    def __repr__(self) -> str:
        return f'<User(id={self.id}, email={self.email}, provider={self.oauth_provider})>'

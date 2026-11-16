import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Text, Enum as SQLEnum, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.generated_resume import GeneratedResume

from app.database import Base
from app.models.user import GUID
import enum


class JDSource(str, enum.Enum):
    PASTE = 'paste'
    UPLOAD = 'upload'


class JobDescription(Base):
    __tablename__ = 'job_descriptions'

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
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    raw_text: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_profile: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    source: Mapped[JDSource] = mapped_column(
        SQLEnum(JDSource, native_enum=False),
        default=JDSource.PASTE,
        nullable=False,
    )
    filename: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    user: Mapped['User'] = relationship('User', back_populates='job_descriptions', lazy='selectin')
    generated_resumes: Mapped[list['GeneratedResume']] = relationship(
        'GeneratedResume',
        back_populates='job_description',
        cascade='all, delete-orphan',
        lazy='selectin',
    )

    __table_args__ = (
        Index('ix_job_descriptions_user_created', 'user_id', 'created_at'),
    )

    def __repr__(self) -> str:
        return f'<JobDescription(id={self.id}, user_id={self.user_id}, title={self.title[:50]})>'

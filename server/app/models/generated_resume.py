import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, ForeignKey, Text, Float, Integer, Index, LargeBinary, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, Dict, Any, List
import enum

from app.database import Base
from app.models.user import GUID


class GenerationStatus(str, enum.Enum):
    pending = 'pending'
    processing = 'processing'
    completed = 'completed'
    failed = 'failed'


class GeneratedResume(Base):
    __tablename__ = 'generated_resumes'

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
    master_resume_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey('master_resumes.id', ondelete='CASCADE'),
        index=True,
        nullable=False,
    )
    job_description_id: Mapped[uuid.UUID] = mapped_column(
        GUID(),
        ForeignKey('job_descriptions.id', ondelete='CASCADE'),
        index=True,
        nullable=False,
    )
    tailored_latex: Mapped[str] = mapped_column(Text, nullable=False)
    pdf_bytes: Mapped[Optional[bytes]] = mapped_column(LargeBinary, nullable=True)
    ats_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    keyword_match: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    missing_keywords: Mapped[List[str]] = mapped_column(JSONB, nullable=False, default=list)
    changes: Mapped[List[str]] = mapped_column(JSONB, nullable=False, default=list)
    ats_notes: Mapped[List[str]] = mapped_column(JSONB, nullable=False, default=list)
    page_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    compile_log: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    llm_provider_used: Mapped[str] = mapped_column(String(50), nullable=False)
    llm_model_used: Mapped[str] = mapped_column(String(100), nullable=False)
    status: Mapped[GenerationStatus] = mapped_column(
        SQLEnum(GenerationStatus),
        default=GenerationStatus.pending,
        nullable=False,
    )
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    generation_time_ms: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
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

    # Relationships
    user: Mapped['User'] = relationship('User', back_populates='generated_resumes', lazy='selectin')
    master_resume: Mapped['MasterResume'] = relationship('MasterResume', back_populates='generated_resumes', lazy='selectin')
    job_description: Mapped['JobDescription'] = relationship('JobDescription', back_populates='generated_resumes', lazy='selectin')

    __table_args__ = (
        Index('ix_generated_resumes_user_created', 'user_id', 'created_at'),
    )

    def __repr__(self) -> str:
        return f'<GeneratedResume(id={self.id}, user_id={self.user_id}, ats_score={self.ats_score}, pages={self.page_count}, status={self.status})>'

import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime, Boolean, ForeignKey, Text, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User
    from app.models.generated_resume import GeneratedResume

from app.database import Base
from app.models.user import GUID


class MasterResume(Base):
    __tablename__ = 'master_resumes'

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
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    latex_source: Mapped[str] = mapped_column(Text, nullable=False)
    parsed_profile: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSONB, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
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

    @property
    def title(self) -> str:
        return self.name

    @title.setter
    def title(self, value: str):
        self.name = value

    # Relationships
    user: Mapped['User'] = relationship('User', back_populates='master_resumes', lazy='selectin')
    generated_resumes: Mapped[list['GeneratedResume']] = relationship(
        'GeneratedResume',
        back_populates='master_resume',
        cascade='all, delete-orphan',
        lazy='selectin',
    )

    __table_args__ = (
        Index('ix_master_resumes_user_default', 'user_id', 'is_default'),
    )

    def __repr__(self) -> str:
        return f'<MasterResume(id={self.id}, user_id={self.user_id}, name={self.name}, default={self.is_default})>'

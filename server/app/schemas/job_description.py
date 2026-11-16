from pydantic import BaseModel, Field, HttpUrl, field_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid


class JobDescriptionCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    raw_text: str = Field(..., min_length=30)
    source: str = Field("paste", pattern="^(paste|upload|manual|file|url)$")
    filename: Optional[str] = Field(None, max_length=500)

    @field_validator("source")
    @classmethod
    def normalize_source(cls, value: str) -> str:
        normalized = (value or "paste").strip().lower()
        if normalized in {"manual", "paste"}:
            return "paste"
        if normalized in {"file", "upload"}:
            return "upload"
        if normalized == "url":
            return "paste"
        return normalized


class JobDescriptionResponse(BaseModel):
    id: uuid.UUID
    title: str
    raw_text: str
    parsed_profile: Optional[Dict[str, Any]] = None
    source: str
    filename: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class JobDescriptionListResponse(BaseModel):
    id: uuid.UUID
    title: str
    source: str
    filename: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
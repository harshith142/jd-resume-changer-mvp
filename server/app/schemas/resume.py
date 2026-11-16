from pydantic import BaseModel, Field, model_validator
from typing import Optional, Dict, Any, List
from datetime import datetime
import uuid


class MasterResumeCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    latex_source: str = Field(..., min_length=100)
    is_default: bool = False

    @model_validator(mode="before")
    @classmethod
    def normalize_name_compat(cls, data):
        if isinstance(data, dict):
            if "title" not in data and "name" in data:
                data["title"] = data["name"]
        return data


class MasterResumeUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    latex_source: Optional[str] = Field(None, min_length=100)
    is_default: Optional[bool] = None

    @model_validator(mode="before")
    @classmethod
    def normalize_name_compat(cls, data):
        if isinstance(data, dict):
            if "title" not in data and "name" in data:
                data["title"] = data["name"]
        return data


class MasterResumeResponse(BaseModel):
    id: uuid.UUID
    title: str
    latex_source: str
    parsed_profile: Optional[Dict[str, Any]] = None
    is_default: bool
    created_at: datetime
    updated_at: datetime

    @property
    def name(self):
        return self.title

    class Config:
        from_attributes = True


class MasterResumeListResponse(BaseModel):
    id: uuid.UUID
    title: str
    is_default: bool
    created_at: datetime
    updated_at: datetime

    @property
    def name(self):
        return self.title

    class Config:
        from_attributes = True
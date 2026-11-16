from pydantic import BaseModel, Field, HttpUrl
from typing import Optional, Literal
from datetime import datetime
import uuid


class LLMProvider(str):
    GEMINI = "gemini"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROK = "grok"
    OPENROUTER = "openrouter"
    NVIDIA = "nvidia"
    OLLAMA = "ollama"


PROVIDER_LITERAL = Literal["gemini", "openai", "anthropic", "grok", "openrouter", "nvidia", "ollama"]


class APIKeyCreate(BaseModel):
    provider: PROVIDER_LITERAL
    api_key: Optional[str] = Field(None, min_length=10, description="The API key (will be encrypted). Not required for Ollama.")
    model: Optional[str] = Field(None, max_length=100)
    ollama_host: Optional[HttpUrl] = Field(None, description="Ollama host URL (for Ollama only)")
    is_session_only: bool = Field(False, description="If true, key not stored in DB, sent per-request")


class APIKeyUpdate(BaseModel):
    api_key: Optional[str] = Field(None, min_length=10)
    model: Optional[str] = Field(None, max_length=100)
    ollama_host: Optional[HttpUrl] = None
    is_session_only: Optional[bool] = None


class APIKeyResponse(BaseModel):
    id: uuid.UUID
    provider: str
    model: Optional[str] = None
    ollama_host: Optional[str] = None
    is_session_only: bool
    has_key: bool  # True if key is stored (not session-only)
    key_preview: Optional[str] = None  # Masked preview of the key (e.g., "••••••••abc123")
    is_valid: Optional[bool] = None  # Last test result
    last_tested_at: Optional[datetime] = None  # When the key was last tested
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class APIKeyTestRequest(BaseModel):
    provider: PROVIDER_LITERAL
    api_key: str
    model: Optional[str] = None
    ollama_host: Optional[HttpUrl] = None


class APIKeyTestResponse(BaseModel):
    success: bool
    message: str
    model_info: Optional[str] = None


# Frontend-compatible test response
class APIKeyTestResult(BaseModel):
    is_valid: bool
    error: Optional[str] = None
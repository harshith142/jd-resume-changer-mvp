from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
import uuid


class KeywordMatch(BaseModel):
    matched_keywords: List[str] = Field(default_factory=list)
    missing_keywords: List[str] = Field(default_factory=list)
    match_percentage: float = 0.0


class GeneratedResumeResponse(BaseModel):
    id: uuid.UUID
    master_resume_id: uuid.UUID
    job_description_id: uuid.UUID
    master_resume_name: Optional[str] = None
    job_description_title: Optional[str] = None
    tailored_latex: str
    pdf_base64: Optional[str] = None
    ats_score: Optional[float] = None
    keyword_match: KeywordMatch
    missing_keywords: List[str] = Field(default_factory=list)
    changes: List[str] = Field(default_factory=list)
    ats_notes: List[str] = Field(default_factory=list)
    page_count: Optional[int] = None
    compile_log: Optional[str] = None
    llm_provider_used: str
    llm_model_used: str
    status: str = "completed"
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    generation_time_ms: Optional[int] = None
    master_resume_title: Optional[str] = None
    jd_title: Optional[str] = None

    class Config:
        from_attributes = True


class GeneratedResumeListResponse(BaseModel):
    id: uuid.UUID
    master_resume_name: Optional[str] = None
    job_description_title: Optional[str] = None
    tailored_latex: Optional[str] = None
    ats_score: Optional[float] = None
    page_count: Optional[int] = None
    llm_provider_used: str
    llm_model_used: str
    created_at: datetime

    class Config:
        from_attributes = True


class GenerateResumeRequest(BaseModel):
    master_resume_id: uuid.UUID
    job_description_id: uuid.UUID
    target_role: Optional[str] = Field(None, max_length=200)
    # Optional: override API key for this request (session-only mode)
    llm_provider: Optional[str] = Field(None, pattern="^(gemini|openai|anthropic|grok|openrouter|nvidia|ollama)$")
    llm_api_key: Optional[str] = None
    llm_model: Optional[str] = None
    llm_ollama_host: Optional[str] = None


class GenerateResumeResponse(BaseModel):
    generated_resume: GeneratedResumeResponse
    # For immediate download without fetching again
    pdf_base64: Optional[str] = None
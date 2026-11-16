from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import List, Optional

from app.database import get_db
from app.api.deps import get_current_user, get_llm_config
from app.services.jd_analyzer import analyze_jd
from app.services.extract_text import extract_text_from_file
from app.models.user import User
from app.models.job_description import JobDescription, JDSource
from app.schemas.job_description import (
    JobDescriptionCreate,
    JobDescriptionResponse,
    JobDescriptionListResponse,
)
from app.schemas.pagination import PaginatedResponse

router = APIRouter(prefix="/job-descriptions", tags=["job-descriptions"])


@router.get("", response_model=PaginatedResponse[JobDescriptionListResponse])
async def list_job_descriptions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    size: int = 20,
):
    """List all job descriptions for the current user."""
    from sqlalchemy import func
    count_result = await db.execute(
        select(func.count(JobDescription.id)).where(JobDescription.user_id == current_user.id)
    )
    total = count_result.scalar() or 0

    offset = (page - 1) * size
    result = await db.execute(
        select(JobDescription)
        .where(JobDescription.user_id == current_user.id)
        .order_by(JobDescription.created_at.desc())
        .limit(size)
        .offset(offset)
    )
    jds = result.scalars().all()

    return PaginatedResponse.create(jds, total, page, size)


@router.post("", response_model=JobDescriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_job_description(
    jd_data: JobDescriptionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new job description from pasted text."""
    llm_config = await get_llm_config(current_user, db)
    parsed_profile = None

    if llm_config["api_key"] or llm_config["provider"] == "ollama":
        try:
            parsed_profile = await analyze_jd(
                jd_data.raw_text,
                llm_config["provider"],
                llm_config["api_key"],
                llm_config["model"],
                llm_config["ollama_host"],
            )
        except Exception:
            pass

    jd = JobDescription(
        user_id=current_user.id,
        title=jd_data.title,
        raw_text=jd_data.raw_text,
        parsed_profile=parsed_profile,
        source=JDSource(jd_data.source),
        filename=jd_data.filename,
    )
    db.add(jd)
    await db.commit()
    await db.refresh(jd)
    return jd


@router.post("/upload", response_model=JobDescriptionResponse, status_code=status.HTTP_201_CREATED)
async def upload_job_description(
    file: UploadFile = File(...),
    title: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a job description from file (PDF, DOCX, TXT)."""
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")

    text = await extract_text_from_file(file.filename, content)
    if len(text) < 30:
        raise HTTPException(status_code=400, detail="File contains less than 30 characters of text")

    if not title:
        title = file.filename or "Untitled Job Description"

    llm_config = await get_llm_config(current_user, db)
    parsed_profile = None
    if llm_config["api_key"] or llm_config["provider"] == "ollama":
        try:
            parsed_profile = await analyze_jd(
                text,
                llm_config["provider"],
                llm_config["api_key"],
                llm_config["model"],
                llm_config["ollama_host"],
            )
        except Exception:
            pass

    jd = JobDescription(
        user_id=current_user.id,
        title=title,
        raw_text=text,
        parsed_profile=parsed_profile,
        source=JDSource.UPLOAD,
        filename=file.filename,
    )
    db.add(jd)
    await db.commit()
    await db.refresh(jd)
    return jd


@router.get("/{jd_id}", response_model=JobDescriptionResponse)
async def get_job_description(
    jd_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific job description."""
    result = await db.execute(
        select(JobDescription).where(
            JobDescription.id == jd_id,
            JobDescription.user_id == current_user.id,
        )
    )
    jd = result.scalar_one_or_none()
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found")
    return jd


@router.delete("/{jd_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_job_description(
    jd_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a job description."""
    result = await db.execute(
        select(JobDescription).where(
            JobDescription.id == jd_id,
            JobDescription.user_id == current_user.id,
        )
    )
    jd = result.scalar_one_or_none()
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found")

    await db.delete(jd)
    await db.commit()
    return None
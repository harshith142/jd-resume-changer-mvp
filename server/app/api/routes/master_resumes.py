from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from typing import List, Optional
import base64

from app.database import get_db
from app.api.deps import get_current_user, get_llm_config
from app.services.resume_parser import analyze_resume
from app.models.user import User
from app.models.master_resume import MasterResume
from app.schemas.resume import (
    MasterResumeCreate,
    MasterResumeUpdate,
    MasterResumeResponse,
    MasterResumeListResponse,
)
from app.schemas.pagination import PaginatedResponse
from app.services.extract_text import extract_text_from_file

router = APIRouter(prefix="/resumes", tags=["master-resumes"])


@router.post("/upload", response_model=MasterResumeResponse, status_code=status.HTTP_201_CREATED)
async def upload_master_resume(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    name: Optional[str] = Form(None),
    is_default: bool = False,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Upload a master resume from file (PDF, DOCX, TXT, or TEX)."""
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:  # 10MB limit
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")

    ext = (file.filename or "").lower().split(".")[-1]
    latex_source = ""

    if ext in ["tex", "latex"]:
        latex_source = content.decode("utf-8", errors="ignore")
    else:
        # Extract text and convert to basic LaTeX template
        text = await extract_text_from_file(file.filename, content)
        latex_source = _text_to_basic_latex(text, file.filename)

    final_title = title or name or file.filename or "Untitled Resume"

    if is_default:
        await db.execute(
            MasterResume.__table__.update()
            .where(MasterResume.user_id == current_user.id)
            .values(is_default=False)
        )

    resume = MasterResume(
        user_id=current_user.id,
        name=final_title,
        latex_source=latex_source,
        is_default=is_default,
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    return resume


@router.get("", response_model=PaginatedResponse[MasterResumeListResponse])
async def list_master_resumes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    size: int = 20,
):
    """List all master resumes for the current user."""
    # Count total
    from sqlalchemy import func
    count_result = await db.execute(
        select(func.count(MasterResume.id)).where(MasterResume.user_id == current_user.id)
    )
    total = count_result.scalar() or 0

    # Get paginated results
    offset = (page - 1) * size
    result = await db.execute(
        select(MasterResume)
        .where(MasterResume.user_id == current_user.id)
        .order_by(MasterResume.is_default.desc(), MasterResume.updated_at.desc())
        .limit(size)
        .offset(offset)
    )
    resumes = result.scalars().all()

    return PaginatedResponse.create(resumes, total, page, size)


@router.post("", response_model=MasterResumeResponse, status_code=status.HTTP_201_CREATED)
async def create_master_resume(
    resume_data: MasterResumeCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new master resume."""
    # If this is set as default, unset other defaults
    if resume_data.is_default:
        await db.execute(
            MasterResume.__table__.update()
            .where(MasterResume.user_id == current_user.id)
            .values(is_default=False)
        )

    # Parse the resume to get structured profile
    llm_config = await get_llm_config(user=current_user, db=db)
    parsed_profile = None
    if llm_config["api_key"] or llm_config["provider"] == "ollama":
        try:
            parsed_profile = await analyze_resume(
                resume_data.latex_source,
                llm_config["provider"],
                llm_config["api_key"],
                llm_config["model"],
                llm_config["ollama_host"],
            )
        except Exception:
            pass

    resume = MasterResume(
        user_id=current_user.id,
        name=resume_data.title,
        latex_source=resume_data.latex_source,
        parsed_profile=parsed_profile,
        is_default=resume_data.is_default,
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    return resume


@router.get("/default", response_model=MasterResumeResponse)
async def get_default_master_resume(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the default master resume."""
    result = await db.execute(
        select(MasterResume)
        .where(MasterResume.user_id == current_user.id, MasterResume.is_default == True)
    )
    resume = result.scalar_one_or_none()
    if not resume:
        # Return the most recent if no default
        result = await db.execute(
            select(MasterResume)
            .where(MasterResume.user_id == current_user.id)
            .order_by(MasterResume.updated_at.desc())
            .limit(1)
        )
        resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="No master resume found")
    return resume


@router.get("/{resume_id}", response_model=MasterResumeResponse)
async def get_master_resume(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific master resume."""
    result = await db.execute(
        select(MasterResume).where(
            MasterResume.id == resume_id,
            MasterResume.user_id == current_user.id,
        )
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Master resume not found")
    return resume


@router.patch("/{resume_id}", response_model=MasterResumeResponse)
async def update_master_resume(
    resume_id: UUID,
    update: MasterResumeUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a master resume."""
    result = await db.execute(
        select(MasterResume).where(
            MasterResume.id == resume_id,
            MasterResume.user_id == current_user.id,
        )
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Master resume not found")

    if update.title is not None:
        resume.name = update.title
    if update.latex_source is not None:
        resume.latex_source = update.latex_source
        # Re-parse if latex changed
        llm_config = await get_llm_config(user=current_user, db=db)
        if llm_config["api_key"] or llm_config["provider"] == "ollama":
            try:
                resume.parsed_profile = await analyze_resume(
                    resume.latex_source,
                    llm_config["provider"],
                    llm_config["api_key"],
                    llm_config["model"],
                    llm_config["ollama_host"],
                )
            except Exception:
                pass
    if update.is_default is not None:
        if update.is_default:
            await db.execute(
                MasterResume.__table__.update()
                .where(MasterResume.user_id == current_user.id)
                .values(is_default=False)
            )
        resume.is_default = update.is_default

    await db.commit()
    await db.refresh(resume)
    return resume


@router.post("/{resume_id}/set-default", response_model=MasterResumeResponse)
async def set_default_master_resume(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Set a master resume as the default."""
    # First, unset any existing default
    await db.execute(
        MasterResume.__table__.update()
        .where(MasterResume.user_id == current_user.id)
        .values(is_default=False)
    )

    # Set the selected resume as default
    result = await db.execute(
        select(MasterResume).where(
            MasterResume.id == resume_id,
            MasterResume.user_id == current_user.id,
        )
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Master resume not found")

    resume.is_default = True
    await db.commit()
    await db.refresh(resume)
    return resume


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_master_resume(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a master resume."""
    result = await db.execute(
        select(MasterResume).where(
            MasterResume.id == resume_id,
            MasterResume.user_id == current_user.id,
        )
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Master resume not found")

    await db.delete(resume)
    await db.commit()
    return None


def _text_to_basic_latex(text: str, filename: Optional[str] = None) -> str:
    """Transform extracted text into a minimal LaTeX-compatible resume body."""
    safe_name = (filename or "resume").replace(".", "_")
    escaped_text = text.replace("\\", "\\textbackslash{}")
    escaped_text = escaped_text.replace("&", "\\&")
    escaped_text = escaped_text.replace("%", "\\%")
    escaped_text = escaped_text.replace("#", "\\#")
    escaped_text = escaped_text.replace("{", "\\{")
    escaped_text = escaped_text.replace("}", "\\}")
    return f"\\documentclass{{article}}\n\\usepackage[margin=1in]{{geometry}}\n\\begin{{document}}\n\\section*{{{safe_name}}}\n{escaped_text}\n\\end{{document}}\n"
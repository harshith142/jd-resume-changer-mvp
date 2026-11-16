from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import List, Optional
import base64
import json
import time

from app.database import get_db
from app.api.deps import get_current_user, get_llm_config
from app.services.matcher import match_resume
from app.services.resume_generator import generate_tailored_resume
from app.services.latex_sanitizer import sanitize_latex, LatexValidationError
from app.services.ats_scorer import compile_tex, calculate_ats_audit
from app.models.user import User
from app.models.master_resume import MasterResume
from app.models.job_description import JobDescription
from app.models.generated_resume import GeneratedResume, GenerationStatus
from app.schemas.generated_resume import (
    GenerateResumeRequest,
    GenerateResumeResponse,
    GeneratedResumeResponse,
    GeneratedResumeListResponse,
    KeywordMatch,
)
from app.schemas.pagination import PaginatedResponse

router = APIRouter(prefix="/generated-resumes", tags=["generated-resumes"])


@router.get("", response_model=PaginatedResponse[GeneratedResumeListResponse])
async def list_generated_resumes(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    size: int = 20,
    master_resume_id: str = None,
    job_description_id: str = None,
):
    """List all generated resumes for the current user."""
    from sqlalchemy import func
    from uuid import UUID

    # Build base query
    base_query = (
        select(GeneratedResume, MasterResume.name, JobDescription.title)
        .join(MasterResume, GeneratedResume.master_resume_id == MasterResume.id)
        .join(JobDescription, GeneratedResume.job_description_id == JobDescription.id)
        .where(GeneratedResume.user_id == current_user.id)
    )

    # Apply filters
    if master_resume_id:
        base_query = base_query.where(GeneratedResume.master_resume_id == UUID(master_resume_id))
    if job_description_id:
        base_query = base_query.where(GeneratedResume.job_description_id == UUID(job_description_id))

    # Count total
    count_query = select(func.count(GeneratedResume.id)).where(GeneratedResume.user_id == current_user.id)
    if master_resume_id:
        count_query = count_query.where(GeneratedResume.master_resume_id == UUID(master_resume_id))
    if job_description_id:
        count_query = count_query.where(GeneratedResume.job_description_id == UUID(job_description_id))

    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    # Get paginated results
    offset = (page - 1) * size
    result = await db.execute(
        base_query
        .order_by(GeneratedResume.created_at.desc())
        .limit(size)
        .offset(offset)
    )
    rows = result.all()

    responses = []
    for gr, mr_name, jd_title in rows:
        responses.append(GeneratedResumeListResponse(
            id=gr.id,
            master_resume_name=mr_name,
            job_description_title=jd_title,
            tailored_latex=gr.tailored_latex,
            ats_score=gr.ats_score,
            page_count=gr.page_count,
            llm_provider_used=gr.llm_provider_used,
            llm_model_used=gr.llm_model_used,
            created_at=gr.created_at,
        ))

    return PaginatedResponse.create(responses, total, page, size)


@router.post("/generate", response_model=GenerateResumeResponse, status_code=status.HTTP_201_CREATED)
async def generate_resume(
    request: GenerateResumeRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Generate a tailored resume from master resume and job description."""
    start_time = time.time()

    # Fetch master resume
    mr_result = await db.execute(
        select(MasterResume).where(
            MasterResume.id == request.master_resume_id,
            MasterResume.user_id == current_user.id,
        )
    )
    master_resume = mr_result.scalar_one_or_none()
    if not master_resume:
        raise HTTPException(status_code=404, detail="Master resume not found")

    # Fetch job description
    jd_result = await db.execute(
        select(JobDescription).where(
            JobDescription.id == request.job_description_id,
            JobDescription.user_id == current_user.id,
        )
    )
    job_description = jd_result.scalar_one_or_none()
    if not job_description:
        raise HTTPException(status_code=404, detail="Job description not found")

    # Get LLM config (from request override or user's stored keys)
    if request.llm_provider and request.llm_api_key:
        llm_config = {
            "provider": request.llm_provider,
            "api_key": request.llm_api_key,
            "model": request.llm_model,
            "ollama_host": request.llm_ollama_host,
        }
    else:
        llm_config = await get_llm_config(http_request, current_user, db)

    if not llm_config["api_key"] and llm_config["provider"] != "ollama":
        raise HTTPException(
            status_code=400,
            detail="No API key configured. Add your API key in Settings or provide one in the request."
        )

    # Create initial record with processing status
    gr = GeneratedResume(
        user_id=current_user.id,
        master_resume_id=master_resume.id,
        job_description_id=job_description.id,
        tailored_latex="",  # Will be updated
        status=GenerationStatus.processing,
        llm_provider_used=llm_config["provider"],
        llm_model_used=llm_config["model"] or "unknown",
    )
    db.add(gr)
    await db.commit()
    await db.refresh(gr)

    try:
        # Step 1: Analyze JD (if not already parsed)
        jd_profile = job_description.parsed_profile
        if not jd_profile:
            from app.services.jd_analyzer import analyze_jd
            jd_profile = await analyze_jd(
                job_description.raw_text,
                llm_config["provider"],
                llm_config["api_key"],
                llm_config["model"],
                llm_config["ollama_host"],
            )
            job_description.parsed_profile = jd_profile
            await db.commit()

        # Step 2: Parse master resume (if not already parsed)
        resume_profile = master_resume.parsed_profile
        if not resume_profile:
            from app.services.resume_parser import analyze_resume
            resume_profile = await analyze_resume(
                master_resume.latex_source,
                llm_config["provider"],
                llm_config["api_key"],
                llm_config["model"],
                llm_config["ollama_host"],
            )
            master_resume.parsed_profile = resume_profile
            await db.commit()

        # Step 3: Match resume to JD
        match_result = await match_resume(
            jd_profile,
            resume_profile,
            llm_config["provider"],
            llm_config["api_key"],
            llm_config["model"],
            llm_config["ollama_host"],
        )

        # Step 4: Generate tailored LaTeX
        generated = await generate_tailored_resume(
            master_resume.latex_source,
            jd_profile,
            match_result,
            llm_config["provider"],
            llm_config["api_key"],
            llm_config["model"],
            llm_config["ollama_host"],
        )

        # Step 5: Sanitize LaTeX
        try:
            clean_latex = sanitize_latex(generated["latex"], master_tex=master_resume.latex_source)
        except LatexValidationError as exc:
            gr.status = GenerationStatus.failed
            gr.error_message = f"LaTeX sanitization failed: {str(exc)}"
            gr.generation_time_ms = int((time.time() - start_time) * 1000)
            await db.commit()
            raise HTTPException(
                status_code=422,
                detail={
                    "message": "LLM generated malformed LaTeX.",
                    "error": str(exc),
                    "stage": "latex_sanitization"
                }
            )

        # Step 6: Compile to PDF
        pdf_path, pages, compile_log = compile_tex(clean_latex)

        # Step 7: Extract PDF text for ATS audit
        import shutil
        import subprocess
        import re
        import tempfile
        from pathlib import Path

        pdf_text = ""
        if shutil.which("pdftotext"):
            with tempfile.TemporaryDirectory() as td:
                txt_out = Path(td) / "text.txt"
                subprocess.run(["pdftotext", str(pdf_path), str(txt_out)], capture_output=True, timeout=15)
                if txt_out.exists():
                    pdf_text = txt_out.read_text(encoding="utf-8", errors="ignore")
        if not pdf_text:
            pdf_text = re.sub(r"\\[a-zA-Z]+(\{[^}]*\})?", " ", clean_latex)

        # Step 8: Run ATS audit
        audit = calculate_ats_audit(pdf_text, job_description.raw_text, pages=pages)

        # Balance LLM score with genuine ATS audit
        llm_score = generated.get("ats_score")
        if llm_score is not None:
            computed_ats = round(0.5 * float(llm_score) + 0.5 * float(audit["ats_score"]))
        else:
            computed_ats = audit["ats_score"]

        matched = audit["matched"]
        missing = audit["missing"]

        ats_insights = generated.get("changes", [])
        ats_insights.append(f"ATS Parseability: {audit['breakdown']['parseability']}/35 | Structure: {audit['breakdown']['structure']}/20 | Keyword Match: {audit['breakdown']['keywords']}/20")
        if audit["quant_rate"] > 0:
            ats_insights.append(f"Quantification metric density: {audit['quant_rate']}% of bullet points contain numbers/metrics.")
        if pages == 1:
            ats_insights.append("PDF length: Exactly 1 page (optimal single-page ATS budget).")
        elif pages:
            ats_insights.append(f"PDF length: {pages} pages (target is 1 page).")

        # Step 9: Encode PDF to base64
        pdf_b64 = base64.b64encode(pdf_path.read_bytes()).decode("ascii")

        # Step 10: Update record with results
        generation_time_ms = int((time.time() - start_time) * 1000)

        # Build proper keyword_match structure for frontend
        keyword_match_obj = KeywordMatch(
            matched_keywords=audit["matched"],
            missing_keywords=audit["missing"],
            match_percentage=audit.get("breakdown", {}).get("keywords", 0) * 5  # rough percentage
        )

        gr.tailored_latex = clean_latex
        gr.pdf_bytes = pdf_path.read_bytes()
        gr.ats_score = computed_ats
        gr.keyword_match = keyword_match_obj.model_dump()
        gr.missing_keywords = missing
        gr.changes = generated.get("changes", [])
        gr.ats_notes = ats_insights
        gr.page_count = pages
        gr.compile_log = compile_log[-4000:]
        gr.llm_provider_used = llm_config["provider"]
        gr.llm_model_used = llm_config["model"] or "unknown"
        gr.status = GenerationStatus.completed
        gr.generation_time_ms = generation_time_ms

        await db.commit()
        await db.refresh(gr)

        return GenerateResumeResponse(
            generated_resume=GeneratedResumeResponse(
                id=gr.id,
                master_resume_id=gr.master_resume_id,
                job_description_id=gr.job_description_id,
                master_resume_title=master_resume.name,
                jd_title=job_description.title,
                tailored_latex=gr.tailored_latex,
                pdf_base64=pdf_b64,
                ats_score=gr.ats_score,
                keyword_match=keyword_match_obj,
                missing_keywords=gr.missing_keywords,
                changes=gr.changes,
                ats_notes=gr.ats_notes,
                page_count=gr.page_count,
                compile_log=gr.compile_log,
                llm_provider_used=gr.llm_provider_used,
                llm_model_used=gr.llm_model_used,
                status=gr.status.value,
                error_message=gr.error_message,
                generation_time_ms=gr.generation_time_ms,
                created_at=gr.created_at,
                updated_at=gr.updated_at,
            ),
            pdf_base64=pdf_b64,
        )

    except HTTPException:
        # Re-raise HTTP exceptions (they already have proper status)
        gr.status = GenerationStatus.failed
        gr.generation_time_ms = int((time.time() - start_time) * 1000)
        await db.commit()
        raise
    except Exception as e:
        gr.status = GenerationStatus.failed
        gr.error_message = str(e)
        gr.generation_time_ms = int((time.time() - start_time) * 1000)
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


@router.post("", response_model=GenerateResumeResponse, status_code=status.HTTP_201_CREATED)
async def generate_resume_compat(
    request: GenerateResumeRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Backward-compatible alias for generation requests."""
    return await generate_resume(request, http_request, current_user, db)


@router.get("/{resume_id}", response_model=GeneratedResumeResponse)
async def get_generated_resume(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific generated resume with full details."""
    result = await db.execute(
        select(GeneratedResume).where(
            GeneratedResume.id == resume_id,
            GeneratedResume.user_id == current_user.id,
        )
    )
    gr = result.scalar_one_or_none()
    if not gr:
        raise HTTPException(status_code=404, detail="Generated resume not found")

    # Fetch master resume and job description for titles
    mr_result = await db.execute(select(MasterResume).where(MasterResume.id == gr.master_resume_id))
    master_resume = mr_result.scalar_one_or_none()

    jd_result = await db.execute(select(JobDescription).where(JobDescription.id == gr.job_description_id))
    job_description = jd_result.scalar_one_or_none()

    pdf_b64 = None
    if gr.pdf_bytes:
        pdf_b64 = base64.b64encode(gr.pdf_bytes).decode("ascii")

    # Convert keyword_match dict to KeywordMatch object if needed
    keyword_match_obj = None
    if gr.keyword_match:
        if isinstance(gr.keyword_match, dict):
            keyword_match_obj = KeywordMatch(**gr.keyword_match)
        else:
            keyword_match_obj = gr.keyword_match

    return GeneratedResumeResponse(
        id=gr.id,
        master_resume_id=gr.master_resume_id,
        job_description_id=gr.job_description_id,
        master_resume_name=master_resume.name if master_resume else "Unknown",
        job_description_title=job_description.title if job_description else "Unknown",
        master_resume_title=master_resume.name if master_resume else "Unknown",
        jd_title=job_description.title if job_description else "Unknown",
        tailored_latex=gr.tailored_latex,
        pdf_base64=pdf_b64,
        ats_score=gr.ats_score,
        keyword_match=keyword_match_obj,
        missing_keywords=gr.missing_keywords,
        changes=gr.changes,
        ats_notes=gr.ats_notes,
        page_count=gr.page_count,
        compile_log=gr.compile_log,
        llm_provider_used=gr.llm_provider_used,
        llm_model_used=gr.llm_model_used,
        status=gr.status.value,
        error_message=gr.error_message,
        generation_time_ms=gr.generation_time_ms,
        updated_at=gr.updated_at,
        created_at=gr.created_at,
    )


@router.get("/{resume_id}/download/pdf")
async def download_pdf(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download PDF file."""
    from fastapi.responses import Response
    result = await db.execute(
        select(GeneratedResume).where(
            GeneratedResume.id == resume_id,
            GeneratedResume.user_id == current_user.id,
        )
    )
    gr = result.scalar_one_or_none()
    if not gr or not gr.pdf_bytes:
        raise HTTPException(status_code=404, detail="PDF not found")

    return Response(
        content=gr.pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="tailored_resume_{resume_id}.pdf"'}
    )


@router.get("/{resume_id}/download/tex")
async def download_tex(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Download LaTeX source."""
    from fastapi.responses import Response
    result = await db.execute(
        select(GeneratedResume).where(
            GeneratedResume.id == resume_id,
            GeneratedResume.user_id == current_user.id,
        )
    )
    gr = result.scalar_one_or_none()
    if not gr:
        raise HTTPException(status_code=404, detail="Resume not found")

    return Response(
        content=gr.tailored_latex,
        media_type="text/plain",
        headers={"Content-Disposition": f'attachment; filename="tailored_resume_{resume_id}.tex"'}
    )


@router.delete("/{resume_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_generated_resume(
    resume_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a generated resume."""
    result = await db.execute(
        select(GeneratedResume).where(
            GeneratedResume.id == resume_id,
            GeneratedResume.user_id == current_user.id,
        )
    )
    gr = result.scalar_one_or_none()
    if not gr:
        raise HTTPException(status_code=404, detail="Generated resume not found")

    await db.delete(gr)
    await db.commit()
    return None
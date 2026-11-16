import json
from typing import Dict, Any, Optional

from app.services.llm_client import call_llm_structured

RESUME_SCHEMA = {
    "type": "object",
    "properties": {
        "candidate_name": {"type": "string"},
        "headline": {"type": "string"},
        "technical_skills": {"type": "array", "items": {"type": "string"}},
        "languages": {"type": "array", "items": {"type": "string"}},
        "frameworks": {"type": "array", "items": {"type": "string"}},
        "databases": {"type": "array", "items": {"type": "string"}},
        "tools": {"type": "array", "items": {"type": "string"}},
        "experience": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "company": {"type": "string"},
                    "role": {"type": "string"},
                    "dates": {"type": "string"},
                    "evidence": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["company", "role", "dates", "evidence"],
            },
        },
        "projects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "dates": {"type": "string"},
                    "technologies": {"type": "array", "items": {"type": "string"}},
                    "evidence": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["name", "dates", "technologies", "evidence"],
            },
        },
        "education": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "program": {"type": "string"},
                    "institute": {"type": "string"},
                    "cgpa": {"type": "string"},
                    "year": {"type": "string"},
                },
                "required": ["program", "institute", "cgpa", "year"],
            },
        },
        "certifications": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "candidate_name",
        "headline",
        "technical_skills",
        "languages",
        "frameworks",
        "databases",
        "tools",
        "experience",
        "projects",
        "education",
        "certifications",
    ],
}


async def analyze_resume(
    latex_source: str,
    provider: str,
    api_key: Optional[str],
    model: Optional[str],
    ollama_host: Optional[str] = None,
) -> Dict[str, Any]:
    """Parse a LaTeX resume and extract structured profile using LLM."""
    prompt = f"""
═══════════════════════════════════════════════════════════════
SYSTEM: MASTER RESUME PROFILE EXTRACTOR
═══════════════════════════════════════════════════════════════

You are a senior resume analyst at a professional career services firm.
Your task is to parse a LaTeX-formatted master resume and produce a
structured, factual candidate profile.

This profile will be the single source of truth used in all subsequent
resume tailoring operations. Accuracy is critical — fabricated or
inferred data will cause legal and reputational harm to the candidate.

───────────────────────────────────────────────────────────────
EXTRACTION RULES (non-negotiable)
───────────────────────────────────────────────────────────────
WHAT TO EXTRACT:
• candidate_name   — Full name exactly as written in the resume header.
• headline         — Professional tagline or current role title if present.
• technical_skills — All skills explicitly listed in the Skills section.
• languages        — Programming/scripting languages only (from Skills).
• frameworks       — Libraries, frameworks, platforms listed in Skills.
• databases        — Database technologies listed in Skills.
• tools            — DevOps, cloud, IDE, testing, or other tools in Skills.
• experience       — Each job: company, role title, dates, and bullet-point
                     evidence EXACTLY as written in the resume.
• projects         — Each project: name, dates, technologies used, and
                     bullet-point evidence EXACTLY as written.
• education        — Each qualification: program, institution, CGPA/grade,
                     and year EXACTLY as written.
• certifications   — Any certifications listed, verbatim.

WHAT NOT TO DO:
✗ Do NOT infer technologies from job titles (e.g. "Java Developer"
  does not prove Java without an explicit mention).
✗ Do NOT add skills from experience bullets to the skills lists
  unless they are explicitly in the Skills section.
✗ Do NOT create achievements, metrics, or summaries not in the resume.
✗ Do NOT paraphrase or clean up — preserve exact company names,
  dates, job titles, and bullet text.
✗ Do NOT add context, commentary, or recommendations.

IMPORTANT: This profile will be used to match the candidate to job
descriptions and generate tailored resumes. Any invented fact will
appear in a real resume sent to real employers.

───────────────────────────────────────────────────────────────
MASTER RESUME (LaTeX source)
───────────────────────────────────────────────────────────────
{latex_source}
""".strip()

    result = await call_llm_structured(prompt, RESUME_SCHEMA, provider, api_key, model, ollama_host)
    return result
import json
from typing import Dict, Any, Optional

from app.services.llm_client import call_llm_structured

JD_SCHEMA = {
    "type": "object",
    "properties": {
        "job_title": {"type": "string"},
        "experience_level": {"type": "string"},
        "must_have_skills": {"type": "array", "items": {"type": "string"}},
        "nice_to_have_skills": {"type": "array", "items": {"type": "string"}},
        "responsibilities": {"type": "array", "items": {"type": "string"}},
        "keywords": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "job_title",
        "experience_level",
        "must_have_skills",
        "nice_to_have_skills",
        "responsibilities",
        "keywords",
    ],
}


async def analyze_jd(
    jd_text: str,
    provider: str,
    api_key: Optional[str],
    model: Optional[str],
    ollama_host: Optional[str] = None,
) -> Dict[str, Any]:
    """Analyze a job description and extract structured intelligence."""
    prompt = f"""
═══════════════════════════════════════════════════════════════
SYSTEM: JOB DESCRIPTION INTELLIGENCE ANALYZER
═══════════════════════════════════════════════════════════════

You are a senior technical recruiter with 15 years of experience
across software engineering, data science, product management,
finance, marketing, operations, and all other industries.

Your task is to extract a structured intelligence profile from the
job description below. This profile will be used to tailor a
candidate's resume for maximum ATS and human-reviewer alignment.

───────────────────────────────────────────────────────────────
EXTRACTION RULES
───────────────────────────────────────────────────────────────
1. Extract ONLY what is explicitly stated or strongly implied by
   the JD text. Never invent requirements.
2. Distinguish "must-have" (required) from "nice-to-have"
   (preferred/bonus) skills precisely — many JDs mark these clearly.
3. For keywords: include technical terms, domain words, tools,
   certifications, soft skills, and industry buzzwords that an ATS
   system would scan for. Think like an ATS engine.
4. Experience level: derive from years mentioned, seniority words
   (junior/mid/senior/lead/principal), or role responsibilities.
5. Responsibilities: use active verb phrases as written in the JD
   (e.g. "Design and implement scalable REST APIs").
6. This works for ALL job types — software, data, product, design,
   finance, marketing, HR, operations, consulting, research, etc.

───────────────────────────────────────────────────────────────
JOB DESCRIPTION
───────────────────────────────────────────────────────────────
{jd_text}
""".strip()

    return await call_llm_structured(prompt, JD_SCHEMA, provider, api_key, model, ollama_host)
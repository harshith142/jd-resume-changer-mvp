import json
from typing import Dict, Any, Optional

from app.services.llm_client import call_llm_structured

MATCH_SCHEMA = {
    "type": "object",
    "properties": {
        "matched_responsibilities": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "jd_responsibility": {"type": "string"},
                    "resume_evidence": {"type": "string"},
                    "match_type": {"type": "string", "enum": ["direct", "related", "missing"]},
                },
                "required": ["jd_responsibility", "resume_evidence", "match_type"],
            },
        },
        "keywords_not_supported": {"type": "array", "items": {"type": "string"}},
        "overall_match": {"type": "number"},
        "matched_skills": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "jd_requirement": {"type": "string"},
                    "resume_evidence": {"type": "string"},
                    "match_type": {"type": "string"},
                },
                "required": ["jd_requirement", "resume_evidence", "match_type"],
            },
        },
        "missing_skills": {"type": "array", "items": {"type": "string"}},
        "related_skills": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "jd_requirement": {"type": "string"},
                    "resume_evidence": {"type": "string"},
                    "reason": {"type": "string"},
                },
                "required": ["jd_requirement", "resume_evidence", "reason"],
            },
        },
        "relevant_experience": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "company": {"type": "string"},
                    "evidence": {"type": "string"},
                    "relevance": {"type": "string"},
                },
                "required": ["company", "evidence", "relevance"],
            },
        },
        "relevant_projects": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "project": {"type": "string"},
                    "evidence": {"type": "string"},
                    "relevance": {"type": "string"},
                },
                "required": ["project", "evidence", "relevance"],
            },
        },
        "keywords_to_emphasize": {"type": "array", "items": {"type": "string"}},
    },
    "required": [
        "overall_match",
        "matched_skills",
        "missing_skills",
        "related_skills",
        "relevant_experience",
        "relevant_projects",
        "keywords_to_emphasize",
        "matched_responsibilities",
        "keywords_not_supported",
    ],
}


async def match_resume(
    jd_profile: Dict[str, Any],
    resume_profile: Dict[str, Any],
    provider: str,
    api_key: Optional[str],
    model: Optional[str],
    ollama_host: Optional[str] = None,
) -> Dict[str, Any]:
    """Match resume profile against job description profile."""
    prompt = f"""
═══════════════════════════════════════════════════════════════
SYSTEM: CANDIDATE-TO-JOB MATCHING ENGINE
═══════════════════════════════════════════════════════════════

You are a senior ATS specialist and recruiter at a global hiring firm.
Your task is to perform a structured, honest compatibility assessment
between a candidate's resume profile and a job description.

This assessment drives the resume tailoring step — any inaccuracy will
produce a dishonest resume that could get the candidate rejected or
blacklisted. Be precise and conservative.

───────────────────────────────────────────────────────────────
MATCHING RULES
───────────────────────────────────────────────────────────────
WHAT TO MATCH:
• Use ONLY skills, tools, and experience explicitly in the resume profile.
• A skill listed in the JD is a DIRECT match only if it appears verbatim
  or near-verbatim in the resume (e.g. "REST API" = "REST APIs" ✓).
• A skill is a RELATED match if the candidate has a demonstrably
  transferable technology (e.g. MySQL → PostgreSQL, Flask → FastAPI).
  Clearly explain the transferability in the reason field.
• A skill is MISSING if the resume has no evidence for it at all.
• A responsibility is MATCHED if the resume contains explicit
  bullet-point evidence supporting it.
• A responsibility is MISSING if no resume evidence supports it.

WHAT NOT TO DO:
✗ Do NOT claim a skill is present just because the job title implies it.
✗ Do NOT mark "Python" as matched if the resume only lists "Django" without
  Python being explicitly mentioned.
✗ Do NOT create or infer experience not in the resume.
✗ Do NOT add any technologies to keywords_to_emphasize that are not in
  the resume — those would be lies on the final resume.

SCORING (overall_match: 0–100):
Calculate a realistic compatibility score using:
  • Must-have skill coverage (40% weight)
  • Relevant work experience alignment (30% weight)
  • Relevant project alignment (20% weight)
  • ATS keyword overlap (10% weight)
This is a compatibility estimate, NOT an employment prediction.

keywords_not_supported: List every JD keyword that has NO resume evidence.
  These will be explicitly excluded from the tailored resume.

keywords_to_emphasize: List only keywords that ARE in the resume and
  align with the JD. These will be naturally woven into the resume.

───────────────────────────────────────────────────────────────
JOB DESCRIPTION PROFILE
───────────────────────────────────────────────────────────────
{json.dumps(jd_profile, indent=2)}

───────────────────────────────────────────────────────────────
CANDIDATE RESUME PROFILE
───────────────────────────────────────────────────────────────
{json.dumps(resume_profile, indent=2)}
""".strip()

    return await call_llm_structured(prompt, MATCH_SCHEMA, provider, api_key, model, ollama_host)
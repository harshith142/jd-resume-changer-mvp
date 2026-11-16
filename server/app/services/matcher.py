import json
import httpx
from typing import Dict, Any, Optional

from app.config import get_settings

settings = get_settings()

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


async def call_llm_structured(
    prompt: str,
    schema: Dict[str, Any],
    provider: str,
    api_key: Optional[str],
    model: Optional[str],
    ollama_host: Optional[str] = None,
) -> Dict[str, Any]:
    if provider == "gemini":
        return await _call_gemini(prompt, schema, api_key, model)
    elif provider == "openrouter":
        return await _call_openrouter(prompt, schema, api_key, model)
    elif provider == "nvidia":
        return await _call_nvidia(prompt, schema, api_key, model)
    elif provider == "ollama":
        return await _call_ollama(prompt, schema, ollama_host, model)
    else:
        raise ValueError(f"Unknown provider: {provider}")


async def _call_gemini(prompt: str, schema: Dict, api_key: str, model: Optional[str]) -> Dict:
    model = model or settings.gemini_model
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": schema,
            "temperature": 0.1,
        },
    }
    async with httpx.AsyncClient(timeout=90) as client:
        resp = await client.post(url, params={"key": api_key}, json=payload)
        resp.raise_for_status()
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text)


async def _call_openrouter(prompt: str, schema: Dict, api_key: str, model: Optional[str]) -> Dict:
    model = model or "meta-llama/llama-3.3-70b-instruct"
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "response_format": {"type": "json_object"},
                "messages": [{"role": "user", "content": prompt + "\nRespond strictly in valid JSON matching the schema."}],
            },
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        return json.loads(content)


async def _call_nvidia(prompt: str, schema: Dict, api_key: str, model: Optional[str]) -> Dict:
    model = model or "nvidia/nemotron-3-ultra-550b-a55b"
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "response_format": {"type": "json_object"},
                "messages": [{"role": "user", "content": prompt + "\nRespond strictly in valid JSON."}],
            },
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        return json.loads(content)


async def _call_ollama(prompt: str, schema: Dict, host: Optional[str], model: Optional[str]) -> Dict:
    host = (host or settings.ollama_host).rstrip("/")
    model = model or settings.ollama_model
    async with httpx.AsyncClient(timeout=180) as client:
        resp = await client.post(
            f"{host}/api/generate",
            json={
                "model": model,
                "prompt": prompt + "\nOutput strictly valid JSON.",
                "format": "json",
                "stream": False,
            },
        )
        resp.raise_for_status()
        raw_json = resp.json().get("response", "{}")
        return json.loads(raw_json)
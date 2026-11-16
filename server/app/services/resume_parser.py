import json
import httpx
from typing import Dict, Any, Optional

from app.config import get_settings

settings = get_settings()

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


async def call_llm_structured(
    prompt: str,
    schema: Dict[str, Any],
    provider: str,
    api_key: Optional[str],
    model: Optional[str],
    ollama_host: Optional[str] = None,
) -> Dict[str, Any]:
    """Call LLM with structured output schema."""
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
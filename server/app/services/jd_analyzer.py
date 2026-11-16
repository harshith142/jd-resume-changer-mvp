import json
import httpx
from typing import Dict, Any, Optional

from app.config import get_settings

settings = get_settings()

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
    async with httpx.AsyncClient(timeout=60) as client:
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
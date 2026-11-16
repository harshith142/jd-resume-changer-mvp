"""Unified LLM client supporting all 7 providers with structured output."""

import json
import httpx
from typing import Dict, Any, Optional

from app.config import get_settings

settings = get_settings()


async def call_llm_structured(
    prompt: str,
    schema: Dict[str, Any],
    provider: str,
    api_key: Optional[str],
    model: Optional[str],
    ollama_host: Optional[str] = None,
) -> Dict[str, Any]:
    """Route to appropriate LLM provider with structured output."""
    if provider == "gemini":
        return await _call_gemini(prompt, schema, api_key, model)
    elif provider == "openai":
        return await _call_openai(prompt, schema, api_key, model)
    elif provider == "anthropic":
        return await _call_anthropic(prompt, schema, api_key, model)
    elif provider == "grok":
        return await _call_grok(prompt, schema, api_key, model)
    elif provider == "openrouter":
        return await _call_openrouter(prompt, schema, api_key, model)
    elif provider == "nvidia":
        return await _call_nvidia(prompt, schema, api_key, model)
    elif provider == "ollama":
        return await _call_ollama(prompt, schema, ollama_host, model)
    else:
        raise ValueError(f"Unknown provider: {provider}")


async def call_llm_text(
    prompt: str,
    provider: str,
    api_key: Optional[str],
    model: Optional[str],
    ollama_host: Optional[str] = None,
    temperature: float = 0.1,
    max_tokens: int = 8192,
) -> str:
    """Route to appropriate LLM provider for plain text output."""
    if provider == "gemini":
        return await _call_gemini_text(prompt, api_key, model, temperature)
    elif provider == "openai":
        return await _call_openai_text(prompt, api_key, model, temperature, max_tokens)
    elif provider == "anthropic":
        return await _call_anthropic_text(prompt, api_key, model, temperature, max_tokens)
    elif provider == "grok":
        return await _call_grok_text(prompt, api_key, model, temperature, max_tokens)
    elif provider == "openrouter":
        return await _call_openrouter_text(prompt, api_key, model, temperature, max_tokens)
    elif provider == "nvidia":
        return await _call_nvidia_text(prompt, api_key, model, temperature, max_tokens)
    elif provider == "ollama":
        return await _call_ollama_text(prompt, ollama_host, model, temperature, max_tokens)
    else:
        raise ValueError(f"Unknown provider: {provider}")


# ============================================================
# GEMINI
# ============================================================
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
    async with httpx.AsyncClient(timeout=180) as client:
        resp = await client.post(url, params={"key": api_key}, json=payload)
        resp.raise_for_status()
        data = resp.json()
        text = data["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(text)


async def _call_gemini_text(prompt: str, api_key: str, model: Optional[str], temperature: float) -> str:
    model = model or settings.gemini_model
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature},
    }
    async with httpx.AsyncClient(timeout=180) as client:
        resp = await client.post(url, params={"key": api_key}, json=payload)
        resp.raise_for_status()
        data = resp.json()
        return data["candidates"][0]["content"]["parts"][0]["text"]


# ============================================================
# OPENAI
# ============================================================
async def _call_openai(prompt: str, schema: Dict, api_key: str, model: Optional[str]) -> Dict:
    """Call OpenAI API with structured output."""
    model = model or settings.openai_model
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": "Respond strictly in valid JSON matching the provided schema."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
            },
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        return json.loads(content)


async def _call_openai_text(prompt: str, api_key: str, model: Optional[str], temperature: float, max_tokens: int) -> str:
    model = model or settings.openai_model
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


# ============================================================
# ANTHROPIC
# ============================================================
async def _call_anthropic(prompt: str, schema: Dict, api_key: str, model: Optional[str]) -> Dict:
    """Call Anthropic Claude API with structured output."""
    model = model or settings.anthropic_model
    async with httpx.AsyncClient(timeout=180) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": model,
                "max_tokens": 8192,
                "temperature": 0.1,
                "system": "Respond strictly in valid JSON matching the provided schema. Do not include any explanations or markdown formatting.",
                "messages": [
                    {"role": "user", "content": prompt + "\n\nRespond strictly in valid JSON matching the schema. No markdown, no explanations."}
                ],
            },
        )
        resp.raise_for_status()
        content = resp.json()["content"][0]["text"]
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        return json.loads(content.strip())


async def _call_anthropic_text(prompt: str, api_key: str, model: Optional[str], temperature: float, max_tokens: int) -> str:
    model = model or settings.anthropic_model
    async with httpx.AsyncClient(timeout=180) as client:
        resp = await client.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": model,
                "max_tokens": max_tokens,
                "temperature": temperature,
                "messages": [{"role": "user", "content": prompt}],
            },
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]


# ============================================================
# GROK (xAI)
# ============================================================
async def _call_grok(prompt: str, schema: Dict, api_key: str, model: Optional[str]) -> Dict:
    """Call Grok (xAI) API with structured output."""
    model = model or settings.grok_model
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            "https://api.x.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "response_format": {"type": "json_object"},
                "messages": [
                    {"role": "system", "content": "Respond strictly in valid JSON matching the provided schema."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
            },
        )
        resp.raise_for_status()
        content = resp.json()["choices"][0]["message"]["content"]
        return json.loads(content)


async def _call_grok_text(prompt: str, api_key: str, model: Optional[str], temperature: float, max_tokens: int) -> str:
    model = model or settings.grok_model
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            "https://api.x.ai/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


# ============================================================
# OPENROUTER
# ============================================================
async def _call_openrouter(prompt: str, schema: Dict, api_key: str, model: Optional[str]) -> Dict:
    model = model or settings.openrouter_model
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


async def _call_openrouter_text(prompt: str, api_key: str, model: Optional[str], temperature: float, max_tokens: int) -> str:
    model = model or settings.openrouter_model
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


# ============================================================
# NVIDIA
# ============================================================
async def _call_nvidia(prompt: str, schema: Dict, api_key: str, model: Optional[str]) -> Dict:
    model = model or settings.nvidia_model
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


async def _call_nvidia_text(prompt: str, api_key: str, model: Optional[str], temperature: float, max_tokens: int) -> str:
    model = model or settings.nvidia_model
    async with httpx.AsyncClient(timeout=120) as client:
        resp = await client.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": max_tokens,
            },
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]


# ============================================================
# OLLAMA
# ============================================================
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


async def _call_ollama_text(prompt: str, host: Optional[str], model: Optional[str], temperature: float, max_tokens: int) -> str:
    host = (host or settings.ollama_host).rstrip("/")
    model = model or settings.ollama_model
    async with httpx.AsyncClient(timeout=180) as client:
        resp = await client.post(
            f"{host}/api/generate",
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": temperature, "num_predict": max_tokens},
            },
        )
        resp.raise_for_status()
        return resp.json().get("response", "")
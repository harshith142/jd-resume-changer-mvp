from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from uuid import UUID
from typing import List, Optional
from datetime import datetime

from app.database import get_db
from app.api.deps import get_current_user, get_llm_config
from app.services.auth import settings
from app.services.encryption import encrypt_api_key, decrypt_api_key, generate_key_fingerprint
from app.models.user import User
from app.models.api_key import APIKey, LLMProvider
from app.schemas.api_key import (
    APIKeyCreate,
    APIKeyUpdate,
    APIKeyResponse,
    APIKeyTestRequest,
    APIKeyTestResponse,
    APIKeyTestResult,
)
from app.schemas.pagination import PaginatedResponse

router = APIRouter(prefix="/api/v1/api-keys", tags=["api-keys"])


def generate_key_preview(decrypted_key: str) -> str:
    """Generate a masked preview of the API key (last 4 chars visible)."""
    if len(decrypted_key) <= 8:
        return "••••••••"
    return "•" * (len(decrypted_key) - 4) + decrypted_key[-4:]


@router.get("", response_model=PaginatedResponse[APIKeyResponse])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    page: int = 1,
    size: int = 20,
):
    """List all API keys for the current user."""

    # Count total
    count_result = await db.execute(
        select(func.count(APIKey.id)).where(APIKey.user_id == current_user.id)
    )
    total = count_result.scalar() or 0

    # Get paginated results
    offset = (page - 1) * size
    result = await db.execute(
        select(APIKey)
        .where(APIKey.user_id == current_user.id)
        .order_by(APIKey.created_at.desc())
        .limit(size)
        .offset(offset)
    )
    keys = result.scalars().all()

    responses = []
    for key in keys:
        has_key = not key.is_session_only and key.key_encrypted is not None
        key_preview = None
        if has_key:
            try:
                decrypted = decrypt_api_key(
                    key.key_encrypted,
                    key.key_nonce,
                    current_user.id,
                    settings.app_secret,
                )
                key_preview = generate_key_preview(decrypted)
            except Exception:
                pass

        responses.append(APIKeyResponse(
            id=key.id,
            provider=key.provider.value,
            model=key.model,
            ollama_host=key.ollama_host,
            is_session_only=key.is_session_only,
            has_key=has_key,
            key_preview=key_preview,
            is_valid=key.is_valid,
            last_tested_at=key.last_tested_at,
            created_at=key.created_at,
            updated_at=key.updated_at,
        ))

    return PaginatedResponse.create(responses, total, page, size)


@router.post("", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    key_data: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create or update an API key for a provider."""
    provider = LLMProvider(key_data.provider)

    # Check if key already exists
    result = await db.execute(
        select(APIKey).where(
            APIKey.user_id == current_user.id,
            APIKey.provider == provider,
        )
    )
    existing = result.scalar_one_or_none()

    if existing:
        # Update existing
        if key_data.api_key:
            if key_data.is_session_only:
                existing.key_encrypted = None
                existing.key_nonce = None
                existing.is_session_only = True
            else:
                encrypted, nonce = encrypt_api_key(
                    key_data.api_key,
                    current_user.id,
                    settings.app_secret,
                )
                existing.key_encrypted = encrypted
                existing.key_nonce = nonce
                existing.is_session_only = False

        if key_data.model is not None:
            existing.model = key_data.model
        if key_data.ollama_host is not None:
            existing.ollama_host = str(key_data.ollama_host)
        if key_data.is_session_only is not None:
            existing.is_session_only = key_data.is_session_only
            if key_data.is_session_only:
                existing.key_encrypted = None
                existing.key_nonce = None

        await db.commit()
        await db.refresh(existing)
        key = existing
    else:
        # Create new
        if key_data.is_session_only:
            key = APIKey(
                user_id=current_user.id,
                provider=provider,
                model=key_data.model,
                ollama_host=str(key_data.ollama_host) if key_data.ollama_host else None,
                is_session_only=True,
            )
        else:
            encrypted, nonce = encrypt_api_key(
                key_data.api_key,
                current_user.id,
                settings.app_secret,
            )
            key = APIKey(
                user_id=current_user.id,
                provider=provider,
                key_encrypted=encrypted,
                key_nonce=nonce,
                model=key_data.model,
                ollama_host=str(key_data.ollama_host) if key_data.ollama_host else None,
                is_session_only=False,
            )
        db.add(key)
        await db.commit()
        await db.refresh(key)

    # Generate key preview since we have the decrypted key
    key_preview = None
    if key_data.api_key and not key.is_session_only:
        try:
            key_preview = generate_key_preview(key_data.api_key)
        except Exception:
            pass

    return APIKeyResponse(
        id=key.id,
        provider=key.provider.value,
        model=key.model,
        ollama_host=key.ollama_host,
        is_session_only=key.is_session_only,
        has_key=not key.is_session_only and key.key_encrypted is not None,
        key_preview=key_preview,
        is_valid=key.is_valid,
        last_tested_at=key.last_tested_at,
        created_at=key.created_at,
        updated_at=key.updated_at,
    )


@router.patch("/{provider}", response_model=APIKeyResponse)
async def update_api_key(
    provider: str,
    key_data: APIKeyUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update an API key."""
    try:
        provider_enum = LLMProvider(provider)
    except ValueError:
        raise HTTPException(status_code=404, detail="Provider not found")

    result = await db.execute(
        select(APIKey).where(
            APIKey.user_id == current_user.id,
            APIKey.provider == provider_enum,
        )
    )
    key = result.scalar_one_or_none()

    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    if key_data.api_key is not None:
        if key_data.is_session_only or (key_data.is_session_only is None and key.is_session_only):
            key.key_encrypted = None
            key.key_nonce = None
            key.is_session_only = True
        else:
            encrypted, nonce = encrypt_api_key(
                key_data.api_key,
                current_user.id,
                settings.app_secret,
            )
            key.key_encrypted = encrypted
            key.key_nonce = nonce
            key.is_session_only = False

    if key_data.model is not None:
        key.model = key_data.model
    if key_data.ollama_host is not None:
        key.ollama_host = str(key_data.ollama_host)
    if key_data.is_session_only is not None:
        key.is_session_only = key_data.is_session_only
        if key_data.is_session_only:
            key.key_encrypted = None
            key.key_nonce = None

    await db.commit()
    await db.refresh(key)

    # Generate key preview if a new key was provided
    key_preview = None
    if key_data.api_key and not key.is_session_only:
        try:
            key_preview = generate_key_preview(key_data.api_key)
        except Exception:
            pass

    return APIKeyResponse(
        id=key.id,
        provider=key.provider.value,
        model=key.model,
        ollama_host=key.ollama_host,
        is_session_only=key.is_session_only,
        has_key=not key.is_session_only and key.key_encrypted is not None,
        key_preview=key_preview,
        is_valid=key.is_valid,
        last_tested_at=key.last_tested_at,
        created_at=key.created_at,
        updated_at=key.updated_at,
    )


@router.get("/{key_id}", response_model=APIKeyResponse)
async def get_api_key(
    key_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific API key by ID."""
    result = await db.execute(
        select(APIKey).where(
            APIKey.id == key_id,
            APIKey.user_id == current_user.id,
        )
    )
    key = result.scalar_one_or_none()

    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    has_key = not key.is_session_only and key.key_encrypted is not None
    key_preview = None
    if has_key:
        try:
            decrypted = decrypt_api_key(
                key.key_encrypted,
                key.key_nonce,
                current_user.id,
                settings.app_secret,
            )
            key_preview = generate_key_preview(decrypted)
        except Exception:
            pass

    return APIKeyResponse(
        id=key.id,
        provider=key.provider.value,
        model=key.model,
        ollama_host=key.ollama_host,
        is_session_only=key.is_session_only,
        has_key=has_key,
        key_preview=key_preview,
        is_valid=key.is_valid,
        last_tested_at=key.last_tested_at,
        created_at=key.created_at,
        updated_at=key.updated_at,
    )


@router.delete("/{provider}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    provider: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete an API key (reverts to session-only)."""
    try:
        provider_enum = LLMProvider(provider)
    except ValueError:
        raise HTTPException(status_code=404, detail="Provider not found")

    result = await db.execute(
        select(APIKey).where(
            APIKey.user_id == current_user.id,
            APIKey.provider == provider_enum,
        )
    )
    key = result.scalar_one_or_none()

    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    # Don't actually delete, just reset to session-only
    key.key_encrypted = None
    key.key_nonce = None
    key.model = None
    key.ollama_host = None
    key.is_session_only = True

    await db.commit()
    return None


@router.post("/{key_id}/test", response_model=APIKeyTestResult)
async def test_stored_api_key(
    key_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Test a stored API key by making a simple request to the provider.
    Returns frontend-compatible format: { is_valid: boolean, error?: string }."""
    result = await db.execute(
        select(APIKey).where(
            APIKey.id == key_id,
            APIKey.user_id == current_user.id,
        )
    )
    key = result.scalar_one_or_none()

    if not key:
        raise HTTPException(status_code=404, detail="API key not found")

    if key.is_session_only or not key.key_encrypted:
        return APIKeyTestResult(is_valid=False, error="No stored key to test (session-only)")

    try:
        decrypted = decrypt_api_key(
            key.key_encrypted,
            key.key_nonce,
            current_user.id,
            settings.app_secret,
        )
    except Exception as e:
        return APIKeyTestResult(is_valid=False, error=f"Failed to decrypt key: {str(e)}")

    provider = key.provider.value
    api_key = decrypted
    model = key.model
    ollama_host = key.ollama_host

    try:
        if provider == "gemini":
            test_result = await _test_gemini(api_key, model or settings.gemini_model)
        elif provider == "openrouter":
            test_result = await _test_openrouter(api_key, model or "meta-llama/llama-3.3-70b-instruct")
        elif provider == "nvidia":
            test_result = await _test_nvidia(api_key, model or "nvidia/nemotron-3-ultra-550b-a55b")
        elif provider == "ollama":
            test_result = await _test_ollama(ollama_host or settings.ollama_host, model or settings.ollama_model)
        else:
            test_result = APIKeyTestResponse(success=False, message="Unknown provider")
    except Exception as e:
        test_result = APIKeyTestResponse(success=False, message=f"Test failed: {str(e)}")

    # Update last_tested_at and is_valid
    key.last_tested_at = datetime.utcnow()
    key.is_valid = test_result.success
    await db.commit()

    if test_result.success:
        return APIKeyTestResult(is_valid=True)
    else:
        return APIKeyTestResult(is_valid=False, error=test_result.message)


@router.post("/test", response_model=APIKeyTestResponse)
async def test_api_key(
    request: APIKeyTestRequest,
    current_user: User = Depends(get_current_user),
):
    """Test an API key by making a simple request to the provider."""
    provider = request.provider
    api_key = request.api_key
    model = request.model
    ollama_host = str(request.ollama_host) if request.ollama_host else None

    try:
        if provider == "gemini":
            return await _test_gemini(api_key, model or settings.gemini_model)
        elif provider == "openrouter":
            return await _test_openrouter(api_key, model or "meta-llama/llama-3.3-70b-instruct")
        elif provider == "nvidia":
            return await _test_nvidia(api_key, model or "nvidia/nemotron-3-ultra-550b-a55b")
        elif provider == "ollama":
            return await _test_ollama(ollama_host or settings.ollama_host, model or settings.ollama_model)
        else:
            return APIKeyTestResponse(success=False, message="Unknown provider")
    except Exception as e:
        return APIKeyTestResponse(success=False, message=f"Test failed: {str(e)}")


async def _test_gemini(api_key: str, model: str) -> APIKeyTestResponse:
    import httpx
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    payload = {
        "contents": [{"parts": [{"text": "Hello"}]}],
        "generationConfig": {"maxOutputTokens": 10},
    }
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(url, json=payload)
        if resp.status_code == 200:
            return APIKeyTestResponse(success=True, message="Connected", model_info=model)
        return APIKeyTestResponse(success=False, message=f"HTTP {resp.status_code}: {resp.text[:200]}")


async def _test_openrouter(api_key: str, model: str) -> APIKeyTestResponse:
    import httpx
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": model, "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 5},
        )
        if resp.status_code == 200:
            return APIKeyTestResponse(success=True, message="Connected", model_info=model)
        return APIKeyTestResponse(success=False, message=f"HTTP {resp.status_code}: {resp.text[:200]}")


async def _test_nvidia(api_key: str, model: str) -> APIKeyTestResponse:
    import httpx
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            "https://integrate.api.nvidia.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={"model": model, "messages": [{"role": "user", "content": "Hi"}], "max_tokens": 5},
        )
        if resp.status_code == 200:
            return APIKeyTestResponse(success=True, message="Connected", model_info=model)
        return APIKeyTestResponse(success=False, message=f"HTTP {resp.status_code}: {resp.text[:200]}")


async def _test_ollama(host: str, model: str) -> APIKeyTestResponse:
    import httpx
    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.post(
            f"{host.rstrip('/')}/api/generate",
            json={"model": model, "prompt": "Hi", "stream": False, "options": {"num_predict": 5}},
        )
        if resp.status_code == 200:
            return APIKeyTestResponse(success=True, message="Connected", model_info=model)
        return APIKeyTestResponse(success=False, message=f"HTTP {resp.status_code}: {resp.text[:200]}")
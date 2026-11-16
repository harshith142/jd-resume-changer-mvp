from typing import Optional, AsyncGenerator
from uuid import UUID
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, timezone

from app.config import get_settings
from app.database import get_db, AsyncSessionLocal
from app.models.user import User, OAuthProvider
from app.models.api_key import APIKey, LLMProvider
from app.services.auth import verify_token, settings, create_user_api_keys
from app.services.encryption import decrypt_api_key

# Security scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Get current authenticated user from JWT token."""
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token_data = verify_token(credentials.credentials, "access")
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.id == token_data.user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_llm_config(
    request: Optional[Request] = None,
    user: Optional[User] = None,
    db: Optional[AsyncSession] = None,
    preferred_provider: Optional[str] = None,
) -> dict:
    """Get LLM configuration for the current request.
    Priority: Request headers > User's stored keys (matching preferred_provider if specified) > Server defaults.
    Accepts both the modern keyworded style and older positional calls.
    """
    if isinstance(request, User):
        user = request
        request = None
    elif isinstance(request, AsyncSession):
        db = request
        request = None

    if isinstance(user, AsyncSession):
        db = user
        user = None

    config = {
        "provider": None,
        "api_key": None,
        "model": None,
        "ollama_host": None,
    }

    if request is not None:
        x_llm_provider = request.headers.get("X-LLM-Provider")
        x_llm_api_key = request.headers.get("X-LLM-API-Key")
        x_llm_model = request.headers.get("X-LLM-Model")
        x_llm_ollama_host = request.headers.get("X-LLM-Ollama-Host")

        if x_llm_provider and x_llm_api_key:
            config["provider"] = x_llm_provider
            config["api_key"] = x_llm_api_key
            config["model"] = x_llm_model
            config["ollama_host"] = x_llm_ollama_host
            return config

        # Also check request body for preferred provider (passed via query or stored in request state)
        if preferred_provider is None and hasattr(request, 'state'):
            preferred_provider = getattr(request.state, 'llm_provider', None)

    if user is None or db is None:
        # No authenticated user: fall back to server defaults
        return _default_llm_config(config)

    # Query for user's stored keys (both session and non-session)
    result = await db.execute(
        select(APIKey).where(APIKey.user_id == user.id)
    )
    stored_keys = result.scalars().all()

    # If user has a preferred provider, try to find that specific key first
    if preferred_provider:
        for key in stored_keys:
            if key.provider.value == preferred_provider:
                # For non-session keys, decrypt the API key
                if not key.is_session_only and key.key_encrypted and key.key_nonce:
                    try:
                        decrypted = decrypt_api_key(
                            key.key_encrypted,
                            key.key_nonce,
                            user.id,
                            settings.app_secret,
                        )
                        config["provider"] = key.provider.value
                        config["api_key"] = decrypted
                        config["model"] = key.model
                        config["ollama_host"] = key.ollama_host
                        return config
                    except Exception:
                        continue
                # For session-only keys (like Ollama), use the stored config directly
                elif key.is_session_only:
                    config["provider"] = key.provider.value
                    config["api_key"] = None  # No API key for Ollama
                    config["model"] = key.model
                    config["ollama_host"] = key.ollama_host
                    return config

    # Otherwise, return the first available non-session key with encrypted key
    for key in stored_keys:
        if not key.is_session_only and key.key_encrypted and key.key_nonce:
            try:
                decrypted = decrypt_api_key(
                    key.key_encrypted,
                    key.key_nonce,
                    user.id,
                    settings.app_secret,
                )
                config["provider"] = key.provider.value
                config["api_key"] = decrypted
                config["model"] = key.model
                config["ollama_host"] = key.ollama_host
                return config
            except Exception:
                continue

    # If no non-session keys, check for session-only keys (e.g., Ollama)
    for key in stored_keys:
        if key.is_session_only:
            config["provider"] = key.provider.value
            config["api_key"] = None
            config["model"] = key.model
            config["ollama_host"] = key.ollama_host
            return config

    return _default_llm_config(config)


def _default_llm_config(config: dict) -> dict:
    if settings.gemini_api_key:
        config["provider"] = "gemini"
        config["api_key"] = settings.gemini_api_key
        config["model"] = settings.gemini_model
    elif settings.openrouter_api_key:
        config["provider"] = "openrouter"
        config["api_key"] = settings.openrouter_api_key
        config["model"] = "meta-llama/llama-3.3-70b-instruct"
    elif settings.nvidia_api_key:
        config["provider"] = "nvidia"
        config["api_key"] = settings.nvidia_api_key
        config["model"] = "nvidia/nemotron-3-ultra-550b-a55b"
    else:
        config["provider"] = "ollama"
        config["api_key"] = None
        config["model"] = settings.ollama_model
        config["ollama_host"] = settings.ollama_host
    return config


async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> Optional[User]:
    """Get current user if authenticated, otherwise None."""
    if not credentials:
        return None

    token_data = verify_token(credentials.credentials, "access")
    if not token_data:
        return None

    result = await db.execute(select(User).where(User.id == token_data.user_id))
    return result.scalar_one_or_none()


async def get_user_api_keys(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[LLMProvider, APIKey]:
    """Get all API keys for the current user, decrypted."""
    result = await db.execute(
        select(APIKey).where(APIKey.user_id == user.id)
    )
    api_keys = result.scalars().all()

    key_map = {}
    for key in api_keys:
        if not key.is_session_only and key.key_encrypted and key.key_nonce:
            try:
                decrypted = decrypt_api_key(
                    key.key_encrypted,
                    key.key_nonce,
                    user.id,
                    settings.app_secret,
                )
                key_map[key.provider] = APIKey(
                    id=key.id,
                    user_id=key.user_id,
                    provider=key.provider,
                    key_encrypted=key.key_encrypted,
                    key_nonce=key.key_nonce,
                    model=key.model,
                    ollama_host=key.ollama_host,
                    is_session_only=key.is_session_only,
                    created_at=key.created_at,
                    updated_at=key.updated_at,
                )
                key_map[key.provider]._decrypted_key = decrypted
            except Exception:
                pass
        elif key.is_session_only:
            key_map[key.provider] = key

    return key_map


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a DB session for background tasks."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
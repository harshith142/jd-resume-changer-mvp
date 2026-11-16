from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import secrets
import uuid
import json
from datetime import datetime, timedelta
from pathlib import Path
from threading import Lock

from app.config import get_settings
from app.database import get_db
from app.schemas.auth import (
    Token,
    GoogleLoginRequest,
    GitHubLoginRequest,
    EmailLoginRequest,
    EmailRegisterRequest,
    RefreshTokenRequest,
    AuthResponse,
)
from app.schemas.user import UserResponse
from app.services.auth import (
    create_access_token,
    create_refresh_token,
    hash_refresh_token,
    hash_password,
    verify_password,
    verify_refresh_token,
    verify_token,
    get_google_auth_url,
    get_github_auth_url,
    exchange_google_code,
    exchange_github_code,
    get_or_create_user,
    create_user_api_keys,
    settings,
)
from app.models.user import User, OAuthProvider
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])

STATE_TTL_SECONDS = 600
STATE_STORE_PATH = Path(__file__).resolve().parents[3] / ".oauth_states.json"
_oauth_state_lock = Lock()

# Persisted state store for OAuth so callback state survives backend restarts.
oauth_states: dict[str, dict] = {}


def _prune_oauth_states() -> None:
    """Remove expired OAuth states and keep the in-memory store lean."""
    now = datetime.utcnow()
    expired = []
    for state, payload in list(oauth_states.items()):
        try:
            created_at = datetime.fromisoformat(payload.get("created_at", "1970-01-01T00:00:00"))
        except (TypeError, ValueError):
            expired.append(state)
            continue
        if now - created_at > timedelta(seconds=STATE_TTL_SECONDS):
            expired.append(state)
    for state in expired:
        oauth_states.pop(state, None)


def _persist_oauth_states() -> None:
    """Persist OAuth state to disk for cross-reload reliability."""
    try:
        with STATE_STORE_PATH.open("w", encoding="utf-8") as fh:
            json.dump(oauth_states, fh)
    except Exception:
        pass


def _load_oauth_states() -> None:
    """Load persisted OAuth state from disk when the server restarts."""
    if not STATE_STORE_PATH.exists():
        return
    try:
        with STATE_STORE_PATH.open("r", encoding="utf-8") as fh:
            stored = json.load(fh)
        if isinstance(stored, dict):
            oauth_states.update(stored)
        _prune_oauth_states()
        _persist_oauth_states()
    except Exception:
        return


def save_oauth_state(state: str, provider: str, redirect_uri: str) -> None:
    """Save OAuth state in a persisted store that survives server restarts."""
    with _oauth_state_lock:
        _load_oauth_states()
        oauth_states[state] = {
            "provider": provider,
            "redirect_uri": redirect_uri,
            "created_at": datetime.utcnow().isoformat(),
        }
        _prune_oauth_states()
        _persist_oauth_states()


def consume_oauth_state(state: str, provider: str) -> dict | None:
    """Consume a stored OAuth state and remove it after callback processing."""
    with _oauth_state_lock:
        _load_oauth_states()
        stored = oauth_states.get(state)
        if not stored or stored.get("provider") != provider:
            _prune_oauth_states()
            _persist_oauth_states()
            return None

        oauth_states.pop(state, None)
        _persist_oauth_states()
        return stored


_load_oauth_states()


class LoginResponse(BaseModel):
    auth_url: str
    state: str


@router.post("/register", response_model=AuthResponse)
async def register_email(
    payload: EmailRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    """Register a user with email and password."""
    email = payload.email.lower().strip()
    result = await db.execute(select(User).where(User.email == email))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="User already exists")

    user = User(
        email=email,
        name=payload.name.strip(),
        password_hash=hash_password(payload.password),
        oauth_provider=None,
        oauth_subject=None,
        last_login=datetime.now(),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    await create_user_api_keys(db, user.id)

    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id, user.email)
    user.refresh_token_hash = hash_refresh_token(refresh_token)
    await db.commit()

    return AuthResponse(
        user=user,
        tokens=Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
        ),
    )


@router.post("/login", response_model=AuthResponse)
async def login_email(
    payload: EmailLoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Login with email and password."""
    email = payload.email.lower().strip()
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalar_one_or_none()
    if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    user.last_login = datetime.now()
    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id, user.email)
    user.refresh_token_hash = hash_refresh_token(refresh_token)
    await db.commit()

    return AuthResponse(
        user=user,
        tokens=Token(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=settings.access_token_expire_minutes * 60,
        ),
    )


@router.get("/login/google", response_model=LoginResponse)
async def login_google(redirect_uri: str):
    """Initiate Google OAuth flow."""
    state = secrets.token_urlsafe(32)
    save_oauth_state(state, "google", redirect_uri)
    auth_url = get_google_auth_url(state, redirect_uri)
    return LoginResponse(auth_url=auth_url, state=state)


@router.get("/login/github", response_model=LoginResponse)
async def login_github(redirect_uri: str):
    """Initiate GitHub OAuth flow."""
    state = secrets.token_urlsafe(32)
    save_oauth_state(state, "github", redirect_uri)
    auth_url = get_github_auth_url(state, redirect_uri)
    return LoginResponse(auth_url=auth_url, state=state)


@router.get("/callback/google")
async def callback_google(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    """Handle Google OAuth callback."""
    stored = consume_oauth_state(state, "google")
    if not stored:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    redirect_uri = stored["redirect_uri"]

    try:
        oauth_subject, email, name, avatar_url = await exchange_google_code(code, redirect_uri)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Google OAuth failed: {str(e)}")

    user = await get_or_create_user(
        db, OAuthProvider.GOOGLE, oauth_subject, email, name, avatar_url
    )

    await create_user_api_keys(db, user.id)

    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id, user.email)

    user.refresh_token_hash = hash_refresh_token(refresh_token)
    await db.commit()

    frontend_url = settings.frontend_url.rstrip("/")
    redirect_url = (
        f"{frontend_url}/callback?access_token={access_token}&refresh_token={refresh_token}"
        f"&callbackUrl=/dashboard"
    )
    return RedirectResponse(url=redirect_url)


@router.get("/callback/github")
async def callback_github(
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    """Handle GitHub OAuth callback."""
    stored = consume_oauth_state(state, "github")
    if not stored:
        raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")

    redirect_uri = stored["redirect_uri"]

    try:
        oauth_subject, email, name, avatar_url = await exchange_github_code(code, redirect_uri)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"GitHub OAuth failed: {str(e)}")

    user = await get_or_create_user(
        db, OAuthProvider.GITHUB, oauth_subject, email, name, avatar_url
    )

    await create_user_api_keys(db, user.id)

    access_token = create_access_token(user.id, user.email)
    refresh_token = create_refresh_token(user.id, user.email)

    user.refresh_token_hash = hash_refresh_token(refresh_token)
    await db.commit()

    frontend_url = settings.frontend_url.rstrip("/")
    redirect_url = (
        f"{frontend_url}/callback?access_token={access_token}&refresh_token={refresh_token}"
        f"&callbackUrl=/dashboard"
    )
    return RedirectResponse(url=redirect_url)


@router.post("/refresh", response_model=Token)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    """Refresh access token using refresh token."""
    token_data = verify_token(request.refresh_token, "refresh")
    if not token_data:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    result = await db.execute(select(User).where(User.id == token_data.user_id))
    user = result.scalar_one_or_none()

    if not user or not user.refresh_token_hash:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    if not verify_refresh_token(request.refresh_token, user.refresh_token_hash):
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    new_access = create_access_token(user.id, user.email)
    new_refresh = create_refresh_token(user.id, user.email)

    user.refresh_token_hash = hash_refresh_token(new_refresh)
    await db.commit()

    return Token(
        access_token=new_access,
        refresh_token=new_refresh,
        expires_in=settings.access_token_expire_minutes * 60,
    )


@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Logout - invalidate refresh token."""
    current_user.refresh_token_hash = None
    await db.commit()
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
):
    """Get current user profile."""
    return current_user


# Add refresh_token_hash column to User model (need to update model)
# This will be done via migration
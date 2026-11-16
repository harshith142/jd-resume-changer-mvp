import uuid
import secrets
import hashlib
import base64
import hmac
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple
from urllib.parse import urlencode

import httpx
from jose import jwt, JWTError
from passlib.context import CryptContext
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.config import get_settings
from app.models.user import User, OAuthProvider
from app.models.api_key import APIKey, LLMProvider
from app.schemas.auth import Token, TokenData
from app.schemas.api_key import APIKeyCreate

settings = get_settings()

# Password hashing for email/password auth - use PBKDF2 to avoid the incompatible bcrypt backend
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def _hash_token_value(token: str) -> str:
    """Normalize a JWT/opaque token before hashing for storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def hash_password(password: str) -> str:
    """Hash a plain-text password using PBKDF2."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against the current or legacy hash formats."""
    if not hashed_password:
        return False

    try:
        return pwd_context.verify(plain_password, hashed_password)
    except Exception:
        # Older or incompatible bcrypt-backed entries can fail at runtime; treat them as invalid.
        return False


def hash_refresh_token(token: str) -> str:
    """Hash a refresh token for storage using PBKDF2 to avoid bcrypt's 72-byte limit with JWTs."""
    normalized = _hash_token_value(token)
    salt = secrets.token_hex(16)
    derived = hashlib.pbkdf2_hmac("sha256", normalized.encode("utf-8"), salt.encode("utf-8"), 200_000)
    return f"pbkdf2_sha256${salt}${base64.b64encode(derived).decode('ascii')}"


def verify_refresh_token(plain: str, hashed: str) -> bool:
    """Verify a refresh token using the same PBKDF2-based scheme."""
    if not hashed or not hashed.startswith("pbkdf2_sha256$"):
        return False

    try:
        _, salt, expected = hashed.split("$", 2)
        normalized = _hash_token_value(plain)
        derived = hashlib.pbkdf2_hmac("sha256", normalized.encode("utf-8"), salt.encode("utf-8"), 200_000)
        actual = base64.b64encode(derived).decode("ascii")
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def create_access_token(user_id: uuid.UUID, email: str) -> str:
    """Create a short-lived JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire,
        "type": "access",
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def create_refresh_token(user_id: uuid.UUID, email: Optional[str] = None) -> str:
    """Create a long-lived refresh token (stored hashed in DB)."""
    expire = datetime.now(timezone.utc) + timedelta(days=settings.refresh_token_expire_days)
    payload = {
        "sub": str(user_id),
        "exp": expire,
        "type": "refresh",
    }
    if email:
        payload["email"] = email
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def verify_token(token: str, token_type: str = "access") -> Optional[TokenData]:
    """Verify and decode a JWT token."""
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        if payload.get("type") != token_type:
            return None
        user_id = uuid.UUID(payload.get("sub"))
        email = payload.get("email")
        exp = datetime.fromtimestamp(payload.get("exp"), tz=timezone.utc)
        return TokenData(user_id=user_id, email=email, exp=exp)
    except (JWTError, ValueError, KeyError):
        return None


# ============================================================
# OAuth Flows
# ============================================================

GOOGLE_AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v3/userinfo"

GITHUB_AUTH_URL = "https://github.com/login/oauth/authorize"
GITHUB_TOKEN_URL = "https://github.com/login/oauth/access_token"
GITHUB_USER_URL = "https://api.github.com/user"
GITHUB_EMAILS_URL = "https://api.github.com/user/emails"


def get_google_auth_url(state: str, redirect_uri: str) -> str:
    """Generate Google OAuth authorization URL."""
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "consent",
    }
    return f"{GOOGLE_AUTH_URL}?{urlencode(params)}"


def get_github_auth_url(state: str, redirect_uri: str) -> str:
    """Generate GitHub OAuth authorization URL."""
    params = {
        "client_id": settings.github_client_id,
        "redirect_uri": redirect_uri,
        "scope": "read:user user:email",
        "state": state,
    }
    return f"{GITHUB_AUTH_URL}?{urlencode(params)}"


async def exchange_google_code(code: str, redirect_uri: str) -> Tuple[str, str, str, str]:
    """
    Exchange Google OAuth code for tokens and user info.
    Returns (oauth_subject, email, name, avatar_url).
    """
    async with httpx.AsyncClient() as client:
        # Exchange code for tokens
        token_resp = await client.post(
            GOOGLE_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code",
            },
            headers={"Accept": "application/json"},
        )
        token_resp.raise_for_status()
        tokens = token_resp.json()

        access_token = tokens.get("access_token")
        if not access_token:
            raise ValueError("No access token in Google response")

        # Get user info
        user_resp = await client.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        user_resp.raise_for_status()
        user_info = user_resp.json()

        oauth_subject = user_info.get("sub")
        email = user_info.get("email")
        name = user_info.get("name", email.split("@")[0] if email else "User")
        avatar_url = user_info.get("picture")

        if not oauth_subject or not email:
            raise ValueError("Missing required user info from Google")

        return oauth_subject, email, name, avatar_url


async def exchange_github_code(code: str, redirect_uri: str) -> Tuple[str, str, str, str]:
    """
    Exchange GitHub OAuth code for tokens and user info.
    Returns (oauth_subject, email, name, avatar_url).
    """
    async with httpx.AsyncClient() as client:
        # Exchange code for access token
        token_resp = await client.post(
            GITHUB_TOKEN_URL,
            data={
                "code": code,
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "redirect_uri": redirect_uri,
            },
            headers={"Accept": "application/json"},
        )
        token_resp.raise_for_status()
        tokens = token_resp.json()

        access_token = tokens.get("access_token")
        if not access_token:
            raise ValueError("No access token in GitHub response")

        # Get user info
        user_resp = await client.get(
            GITHUB_USER_URL,
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        )
        user_resp.raise_for_status()
        user_info = user_resp.json()

        # Get primary email
        email_resp = await client.get(
            GITHUB_EMAILS_URL,
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
        )
        email_resp.raise_for_status()
        emails = email_resp.json()

        primary_email = next(
            (e["email"] for e in emails if e.get("primary") and e.get("verified")),
            emails[0]["email"] if emails else None,
        )

        oauth_subject = str(user_info.get("id"))
        email = primary_email or f"{user_info.get('login')}@github.local"
        name = user_info.get("name") or user_info.get("login") or "User"
        avatar_url = user_info.get("avatar_url")

        if not oauth_subject:
            raise ValueError("Missing required user info from GitHub")

        return oauth_subject, email, name, avatar_url


async def get_or_create_user(
    db: AsyncSession,
    provider: OAuthProvider,
    oauth_subject: str,
    email: str,
    name: str,
    avatar_url: Optional[str] = None,
) -> User:
    """Get existing user or create new one from OAuth."""
    # Try to find by OAuth provider + subject
    result = await db.execute(
        select(User).where(
            User.oauth_provider == provider,
            User.oauth_subject == oauth_subject,
        )
    )
    user = result.scalar_one_or_none()

    if user:
        # Update last login and avatar if changed
        user.last_login = datetime.now(timezone.utc)
        if avatar_url and user.avatar_url != avatar_url:
            user.avatar_url = avatar_url
        await db.commit()
        await db.refresh(user)
        return user

    # Check if email already exists with different provider
    result = await db.execute(select(User).where(User.email == email))
    existing = result.scalar_one_or_none()

    if existing:
        # Link OAuth to existing account
        existing.oauth_provider = provider
        existing.oauth_subject = oauth_subject
        existing.last_login = datetime.now(timezone.utc)
        if avatar_url:
            existing.avatar_url = avatar_url
        await db.commit()
        await db.refresh(existing)
        return existing

    # Create new user
    user = User(
        email=email,
        name=name,
        avatar_url=avatar_url,
        oauth_provider=provider,
        oauth_subject=oauth_subject,
        last_login=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def create_user_api_keys(db: AsyncSession, user_id: uuid.UUID) -> list[APIKey]:
    """Create default API key entries for a user without duplicating existing provider rows."""
    api_keys = []
    for provider in LLMProvider:
        existing = await db.execute(
            select(APIKey).where(
                APIKey.user_id == user_id,
                APIKey.provider == provider,
            )
        )
        if existing.scalar_one_or_none() is not None:
            continue

        api_key = APIKey(
            user_id=user_id,
            provider=provider,
            is_session_only=True,
        )
        db.add(api_key)
        api_keys.append(api_key)
    await db.commit()
    for key in api_keys:
        await db.refresh(key)
    return api_keys
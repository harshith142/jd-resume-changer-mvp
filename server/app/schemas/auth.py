from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Literal
from datetime import datetime
import uuid


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class TokenData(BaseModel):
    user_id: uuid.UUID
    email: Optional[EmailStr] = None
    exp: datetime


class GoogleLoginRequest(BaseModel):
    code: str
    redirect_uri: str


class GitHubLoginRequest(BaseModel):
    code: str
    redirect_uri: str


class EmailLoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)


class EmailRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6)
    name: str = Field(..., min_length=1, max_length=255)


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class AuthResponse(BaseModel):
    user: "UserResponse"
    tokens: Token


# Forward reference
from app.schemas.user import UserResponse
AuthResponse.model_rebuild()
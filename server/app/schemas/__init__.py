from app.schemas.auth import *
from app.schemas.user import *
from app.schemas.api_key import *
from app.schemas.resume import *
from app.schemas.job_description import *
from app.schemas.pagination import *

__all__ = [
    # auth
    "Token",
    "TokenData",
    "GoogleLoginRequest",
    "GitHubLoginRequest",
    "RefreshTokenRequest",
    # user
    "UserResponse",
    "UserUpdate",
    # api_key
    "APIKeyCreate",
    "APIKeyUpdate",
    "APIKeyResponse",
    "APIKeyTestRequest",
    "APIKeyTestResponse",
    # resume
    "MasterResumeCreate",
    "MasterResumeUpdate",
    "MasterResumeResponse",
    "MasterResumeListResponse",
    # job_description
    "JobDescriptionCreate",
    "JobDescriptionResponse",
    "JobDescriptionListResponse",
    # generated_resume
    "GeneratedResumeCreate",
    "GeneratedResumeResponse",
    "GeneratedResumeListResponse",
    "GenerateResumeRequest",
    "GenerateResumeResponse",
    # pagination
    "PaginatedResponse",
]
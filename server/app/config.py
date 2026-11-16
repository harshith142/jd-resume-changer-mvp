from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
import secrets


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Database - Use SQLite for local dev if postgres not available
    database_url: str = "sqlite+aiosqlite:///./jd_resume_changer.db"

    # Redis - optional for local dev
    redis_url: str = ""

    # App Security
    app_secret: str = ""  # 32-char base64 for API key encryption
    jwt_secret: str = ""  # JWT signing secret
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 15
    refresh_token_expire_days: int = 30

    # OAuth - Google
    google_client_id: str = ""
    google_client_secret: str = ""

    # OAuth - GitHub
    github_client_id: str = ""
    github_client_secret: str = ""

    # Frontend URL (CORS, redirects)
    frontend_url: str = "http://localhost:3000"

    # Server
    host: str = "0.0.0.0"
    port: int = 8000
    environment: str = "development"

    # LLM Provider defaults (fallback if user doesn't provide keys)
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"
    openrouter_api_key: str = ""
    nvidia_api_key: str = ""
    ollama_host: str = "http://127.0.0.1:11434"
    ollama_model: str = "llama3.2:latest"

    # File upload
    max_upload_size_mb: int = 10

    # Rate limiting
    rate_limit_requests: int = 60
    rate_limit_window_seconds: int = 60

    @property
    def cors_origins(self) -> list[str]:
        origins = [self.frontend_url]
        if self.environment == "development":
            origins.extend([
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:8000",
                "http://127.0.0.1:8000",
            ])
        return origins


@lru_cache()
def get_settings() -> Settings:
    return Settings()
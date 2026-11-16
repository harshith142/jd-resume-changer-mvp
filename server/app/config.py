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

    # ============================================
    # LLM Provider API Keys & Model Names
    # ============================================

    # Google Gemini
    gemini_api_key: str = ""
    gemini_model: str = "gemini-1.5-flash"

    # OpenAI
    openai_api_key: str = ""
    openai_model: str = "gpt-4o-mini"

    # Anthropic Claude
    anthropic_api_key: str = ""
    anthropic_model: str = "claude-3-5-haiku-20241022"

    # Grok (xAI)
    grok_api_key: str = ""
    grok_model: str = "grok-beta"

    # OpenRouter (multi-provider gateway)
    openrouter_api_key: str = ""
    openrouter_model: str = "meta-llama/llama-3.3-70b-instruct"

    # NVIDIA NIM
    nvidia_api_key: str = ""
    nvidia_model: str = "nvidia/nemotron-3-ultra-550b-a55b"

    # Ollama (local)
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
                "http://localhost:8765",
                "http://127.0.0.1:8765",
            ])
        return origins

    def get_llm_providers(self) -> dict:
        """Return dict of configured LLM providers with their keys and default models."""
        providers = {}

        if self.gemini_api_key:
            providers["gemini"] = {
                "api_key": self.gemini_api_key,
                "model": self.gemini_model,
                "name": "Google Gemini"
            }

        if self.openai_api_key:
            providers["openai"] = {
                "api_key": self.openai_api_key,
                "model": self.openai_model,
                "name": "OpenAI"
            }

        if self.anthropic_api_key:
            providers["anthropic"] = {
                "api_key": self.anthropic_api_key,
                "model": self.anthropic_model,
                "name": "Anthropic Claude"
            }

        if self.grok_api_key:
            providers["grok"] = {
                "api_key": self.grok_api_key,
                "model": self.grok_model,
                "name": "Grok (xAI)"
            }

        if self.openrouter_api_key:
            providers["openrouter"] = {
                "api_key": self.openrouter_api_key,
                "model": self.openrouter_model,
                "name": "OpenRouter"
            }

        if self.nvidia_api_key:
            providers["nvidia"] = {
                "api_key": self.nvidia_api_key,
                "model": self.nvidia_model,
                "name": "NVIDIA NIM"
            }

        # Ollama doesn't need an API key
        providers["ollama"] = {
            "api_key": None,
            "model": self.ollama_model,
            "host": self.ollama_host,
            "name": "Ollama (Local)"
        }

        return providers


@lru_cache()
def get_settings() -> Settings:
    return Settings()
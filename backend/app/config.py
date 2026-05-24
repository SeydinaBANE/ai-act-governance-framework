from __future__ import annotations

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # App
    environment: str = "development"
    log_level: str = "INFO"

    # JWT
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 480

    # Database
    database_url: str

    # OpenRouter
    openrouter_api_key: str = ""
    openrouter_model: str = "anthropic/claude-haiku-4.5"
    openrouter_base_url: str = "https://openrouter.ai/api/v1"

    # Presidio
    presidio_analyzer_url: str = "http://presidio-analyzer:3000"
    presidio_anonymizer_url: str = "http://presidio-anonymizer:3001"
    presidio_confidence_threshold: float = 0.85

    # CORS
    allowed_origins: list[str] = ["http://localhost:3000"]

    # Upload
    max_upload_size_mb: int = 10
    upload_dir: str = "/app/uploads"

    @field_validator("allowed_origins", mode="before")
    @classmethod
    def parse_origins(cls, v: str | list[str]) -> list[str]:
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",")]
        return v

    @property
    def is_production(self) -> bool:
        return self.environment == "production"


settings = Settings()

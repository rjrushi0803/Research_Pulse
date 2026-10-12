"""Centralized application settings.

Configuration comes from environment variables or an optional local `.env` file.
Keep secrets out of source control; production deployments should inject them securely.
"""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed settings shared across the application."""

    app_name: str = "Research_Pulse"
    app_env: Literal["development", "test", "staging", "production"] = "development"
    log_level: str = Field(default="INFO", pattern=r"^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$")
    host: str = "127.0.0.1"
    port: int = Field(default=8000, ge=1, le=65535)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return one cached settings instance for this process.
    Caching avoids re-reading configuration for every request. Tests can call
    `get_settings.cache_clear()` when they need a fresh configuration instance.
    """
    return Settings()

"""Application configuration loaded from environment variables."""

from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Typed configuration sourced from .env or environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Adzuna
    adzuna_app_id: str = Field(..., description="Adzuna application ID")
    adzuna_app_key: str = Field(..., description="Adzuna application key")

    # JSearch (optional — graceful degradation if quota exhausted)
    jsearch_api_key: str | None = Field(default=None, description="RapidAPI key for JSearch")

    # Storage
    duckdb_path: Path = Field(
        default=Path("data/jobhunt.duckdb"),
        description="Filesystem path to the DuckDB database",
    )

    # Logging
    log_level: str = Field(default="INFO", description="Python logging level")


# Single shared instance, imported elsewhere as `from jobhunt.config import settings`
settings = Settings()  # type: ignore[call-arg]

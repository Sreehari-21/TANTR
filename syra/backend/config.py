"""
SYRA Backend - Configuration (development / staging / production).
"""

from __future__ import annotations

import json
from typing import Any, List, Literal, Optional

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


def _parse_cors(v: Any) -> List[str]:
    if v is None:
        return ["http://localhost:3000", "http://localhost:3001"]
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    if isinstance(v, str):
        s = v.strip()
        if s.startswith("["):
            try:
                parsed = json.loads(s)
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed if str(x).strip()]
            except json.JSONDecodeError:
                pass
        return [x.strip() for x in s.split(",") if x.strip()]
    return ["http://localhost:3000", "http://localhost:3001"]


def _parse_hosts(v: Any) -> Optional[List[str]]:
    if v is None or v == "":
        return None
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()] or None
    if isinstance(v, str):
        parts = [x.strip() for x in v.split(",") if x.strip()]
        return parts or None
    return None


class Settings(BaseSettings):
    """Application settings from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    ENVIRONMENT: Literal["development", "staging", "production"] = "development"

    APP_NAME: str = "SYRA"
    DEBUG: bool = False

    DATABASE_URL: str = "postgresql://syra:syra@localhost:5432/syra"
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_PRE_PING: bool = True

    REDIS_URL: str = "redis://localhost:6379/0"

    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"

    # Grading rubric (must sum to 1.0)
    GRADE_WEIGHT_QUALITY: float = 0.30
    GRADE_WEIGHT_EFFICIENCY: float = 0.25
    GRADE_WEIGHT_DOCUMENTATION: float = 0.20
    GRADE_WEIGHT_TESTING: float = 0.15
    GRADE_WEIGHT_CONSISTENCY: float = 0.10

    # Blend AI overall score into final grade (0 = metrics only, 1 = AI only)
    GRADE_AI_BLEND: float = 0.30

    # Run pytest when test files are present (static fallback if unavailable)
    RUN_PYTEST_ON_ANALYZE: bool = True
    PYTEST_TIMEOUT_SECONDS: int = 20

    REPOS_BASE_PATH: str = "./repos"

    CORS_ORIGINS: List[str] = Field(
        default_factory=lambda: ["http://localhost:3000", "http://localhost:3001"]
    )

    TRUSTED_HOSTS: Optional[List[str]] = None

    # Development: create tables with SQLAlchemy (never use in production)
    DEV_AUTO_CREATE_SCHEMA: bool = True

    # Run Alembic migrations when the API process starts
    RUN_MIGRATIONS_ON_STARTUP: bool = False

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def cors_origins(cls, v: Any) -> List[str]:
        return _parse_cors(v)

    @field_validator("TRUSTED_HOSTS", mode="before")
    @classmethod
    def trusted_hosts(cls, v: Any) -> Optional[List[str]]:
        return _parse_hosts(v)

    @model_validator(mode="after")
    def validate_environment(self) -> "Settings":
        if self.ENVIRONMENT in ("production", "staging"):
            forbidden = {
                "change-me-in-production",
                "secret",
                "changeme",
                "your-secret-key-change-in-production",
            }
            key = self.SECRET_KEY.strip()
            if len(key) < 32 or key.lower() in forbidden:
                raise ValueError(
                    "For staging/production, set SECRET_KEY to a random string of at least 32 characters "
                    "(e.g. openssl rand -hex 32)."
                )
            if self.ENVIRONMENT == "production" and self.DEBUG:
                raise ValueError("DEBUG must be false when ENVIRONMENT=production.")
            if self.ENVIRONMENT == "production" and self.DEV_AUTO_CREATE_SCHEMA:
                raise ValueError(
                    "Set DEV_AUTO_CREATE_SCHEMA=false in production. Apply schema with: alembic upgrade head"
                )
        return self


settings = Settings()

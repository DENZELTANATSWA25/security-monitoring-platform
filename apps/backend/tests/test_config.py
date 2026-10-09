"""Tests for application runtime configuration."""

import pytest
from pydantic import ValidationError

from app.core.config import Settings


def build_settings(**overrides: object) -> Settings:
    """Create isolated settings without reading the developer .env file."""

    values = {
        "DATABASE_URL": (
            "postgresql+asyncpg://test:test@postgres:5432/test_db"
        ),
        "REDIS_URL": "redis://redis:6379/1",
        "JWT_SECRET_KEY": "test-secret",
        "_env_file": None,
    }

    values.update(overrides)

    return Settings(**values)


def test_cors_origins_are_parsed() -> None:
    settings = build_settings(
        CORS_ORIGINS=(
            "https://security.example.com,"
            "https://admin.example.com"
        )
    )

    assert settings.cors_origins == [
        "https://security.example.com",
        "https://admin.example.com",
    ]


def test_cors_origins_ignore_whitespace_and_empty_values() -> None:
    settings = build_settings(
        CORS_ORIGINS=(
            " https://security.example.com, ,"
            "https://admin.example.com "
        )
    )

    assert settings.cors_origins == [
        "https://security.example.com",
        "https://admin.example.com",
    ]


def test_environment_is_normalized() -> None:
    settings = build_settings(
        APP_ENV="PRODUCTION",
    )

    assert settings.APP_ENV == "production"


def test_unknown_environment_is_rejected() -> None:
    with pytest.raises(ValidationError):
        build_settings(
            APP_ENV="somewhere",
        )


def test_empty_jwt_secret_is_rejected() -> None:
    with pytest.raises(ValidationError):
        build_settings(
            JWT_SECRET_KEY="   ",
        )
"""Tests for interactive login rate limiting."""

from httpx import AsyncClient

from app.core.config import settings
from app.models.user import User


async def test_login_requests_within_limit_are_allowed(
    client: AsyncClient,
    viewer_user: User,
    monkeypatch,
) -> None:
    """Requests below the configured threshold should reach authentication."""

    monkeypatch.setattr(
        settings,
        "LOGIN_RATE_LIMIT_PER_EMAIL",
        3,
    )
    monkeypatch.setattr(
        settings,
        "LOGIN_RATE_LIMIT_PER_IP",
        10,
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": viewer_user.email,
            "password": "DefinitelyWrongPassword!",
        },
    )

    assert response.status_code == 401


async def test_login_rate_limit_blocks_repeated_email_requests(
    client: AsyncClient,
    viewer_user: User,
    monkeypatch,
) -> None:
    """Repeated login requests for one account should eventually be blocked."""

    monkeypatch.setattr(
        settings,
        "LOGIN_RATE_LIMIT_PER_EMAIL",
        2,
    )
    monkeypatch.setattr(
        settings,
        "LOGIN_RATE_LIMIT_PER_IP",
        100,
    )

    credentials = {
        "email": viewer_user.email,
        "password": "DefinitelyWrongPassword!",
    }

    first = await client.post(
        "/api/v1/auth/login",
        json=credentials,
    )
    second = await client.post(
        "/api/v1/auth/login",
        json=credentials,
    )
    blocked = await client.post(
        "/api/v1/auth/login",
        json=credentials,
    )

    assert first.status_code == 401
    assert second.status_code == 401

    assert blocked.status_code == 429
    assert blocked.json()["detail"] == (
        "Too many login attempts. Try again later."
    )
    assert "Retry-After" in blocked.headers


async def test_login_rate_limit_normalizes_email(
    client: AsyncClient,
    viewer_user: User,
    monkeypatch,
) -> None:
    """Email casing must not bypass the per-account limiter."""

    monkeypatch.setattr(
        settings,
        "LOGIN_RATE_LIMIT_PER_EMAIL",
        1,
    )
    monkeypatch.setattr(
        settings,
        "LOGIN_RATE_LIMIT_PER_IP",
        100,
    )

    first = await client.post(
        "/api/v1/auth/login",
        json={
            "email": viewer_user.email,
            "password": "DefinitelyWrongPassword!",
        },
    )

    blocked = await client.post(
        "/api/v1/auth/login",
        json={
            "email": viewer_user.email.upper(),
            "password": "DefinitelyWrongPassword!",
        },
    )

    assert first.status_code == 401
    assert blocked.status_code == 429


async def test_login_rate_limit_blocks_repeated_ip_requests(
    client: AsyncClient,
    monkeypatch,
) -> None:
    """Changing account identifiers must not bypass the client-IP limit."""

    monkeypatch.setattr(
        settings,
        "LOGIN_RATE_LIMIT_PER_EMAIL",
        100,
    )
    monkeypatch.setattr(
        settings,
        "LOGIN_RATE_LIMIT_PER_IP",
        2,
    )

    for index in range(2):
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": f"unknown{index}@example.com",
                "password": "DefinitelyWrongPassword!",
            },
        )

        assert response.status_code == 401

    blocked = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "another@example.com",
            "password": "DefinitelyWrongPassword!",
        },
    )

    assert blocked.status_code == 429
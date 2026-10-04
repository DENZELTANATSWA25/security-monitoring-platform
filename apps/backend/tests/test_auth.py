"""Authentication and role-based access-control tests."""

from httpx import AsyncClient

from app.models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.login_attempt import LoginAttempt
from app.services.location_service import GeoLocation

async def test_valid_login_returns_access_token(
    client: AsyncClient,
    viewer_user: User,
) -> None:
    """A user with valid credentials should receive a bearer token."""

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": viewer_user.email,
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["access_token"]
    assert body["token_type"] == "bearer"

async def test_login_persists_resolved_location(
    client: AsyncClient,
    viewer_user: User,
    db_session: AsyncSession,
    monkeypatch,
) -> None:
    """Resolved IP coordinates should be stored with the login attempt."""

    async def fake_resolve_ip_location(
        ip_address: str | None,
    ) -> GeoLocation:
        assert ip_address is not None

        return GeoLocation(
            latitude=51.5074,
            longitude=-0.1278,
        )

    monkeypatch.setattr(
        "app.api.v1.endpoints.auth.resolve_ip_location",
        fake_resolve_ip_location,
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": viewer_user.email,
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 200

    result = await db_session.execute(
        select(LoginAttempt)
        .where(
            LoginAttempt.email == viewer_user.email,
            LoginAttempt.successful.is_(True),
        )
        .order_by(LoginAttempt.id.desc())
        .limit(1)
    )

    attempt = result.scalar_one()

    assert attempt.latitude == 51.5074
    assert attempt.longitude == -0.1278

async def test_login_succeeds_without_resolved_location(
    client: AsyncClient,
    viewer_user: User,
    db_session: AsyncSession,
    monkeypatch,
) -> None:
    """Authentication should continue when an IP has no resolved location."""

    async def fake_resolve_ip_location(
        ip_address: str | None,
    ) -> None:
        return None

    monkeypatch.setattr(
        "app.api.v1.endpoints.auth.resolve_ip_location",
        fake_resolve_ip_location,
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": viewer_user.email,
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 200

    result = await db_session.execute(
        select(LoginAttempt)
        .where(
            LoginAttempt.email == viewer_user.email,
            LoginAttempt.successful.is_(True),
        )
        .order_by(LoginAttempt.id.desc())
        .limit(1)
    )

    attempt = result.scalar_one()

    assert attempt.latitude is None
    assert attempt.longitude is None


async def test_wrong_password_is_rejected(
    client: AsyncClient,
    viewer_user: User,
) -> None:
    """Invalid credentials should not authenticate."""

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": viewer_user.email,
            "password": "DefinitelyWrongPassword!",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"


async def test_login_ignores_forwarded_ip_from_untrusted_peer(
    client: AsyncClient,
    viewer_user: User,
    db_session: AsyncSession,
    monkeypatch,
) -> None:
    """An untrusted client must not spoof its login IP using X-Forwarded-For."""

    monkeypatch.setattr(
        settings,
        "TRUSTED_PROXY_IPS",
        "",
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": viewer_user.email,
            "password": "TestPassword123!",
        },
        headers={
            "X-Forwarded-For": "8.8.8.8",
        },
    )

    assert response.status_code == 200

    result = await db_session.execute(
        select(LoginAttempt)
        .where(
            LoginAttempt.email == viewer_user.email,
            LoginAttempt.successful.is_(True),
        )
        .order_by(LoginAttempt.id.desc())
        .limit(1)
    )

    attempt = result.scalar_one()

    assert attempt.ip_address != "8.8.8.8"

async def test_login_accepts_forwarded_ip_from_trusted_proxy(
    client: AsyncClient,
    viewer_user: User,
    db_session: AsyncSession,
    monkeypatch,
) -> None:
    """A trusted immediate proxy may provide the original client IP."""

    monkeypatch.setattr(
        settings,
        "TRUSTED_PROXY_IPS",
        "127.0.0.1",
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": viewer_user.email,
            "password": "TestPassword123!",
        },
        headers={
            "X-Forwarded-For": "8.8.8.8",
        },
    )

    assert response.status_code == 200

    result = await db_session.execute(
        select(LoginAttempt)
        .where(
            LoginAttempt.email == viewer_user.email,
            LoginAttempt.successful.is_(True),
        )
        .order_by(LoginAttempt.id.desc())
        .limit(1)
    )

    attempt = result.scalar_one()

    assert attempt.ip_address == "8.8.8.8"
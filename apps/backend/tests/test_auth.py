"""Authentication and role-based access-control tests."""

from httpx import AsyncClient

from app.models.user import User
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timezone

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

async def test_successful_login_updates_last_login(
    client: AsyncClient,
    viewer_user: User,
    db_session: AsyncSession,
) -> None:
    """Successful authentication should persist the last login time."""

    # Capture the ID before expiring ORM objects.
    user_id = viewer_user.id

    before_login = datetime.now(timezone.utc).replace(tzinfo=None)

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": viewer_user.email,
            "password": "TestPassword123!",
        },
    )

    assert response.status_code == 200

    # Expire cached ORM state so the next query reads the database.
    db_session.expire_all()

    result = await db_session.execute(
        select(User).where(User.id == user_id)
    )

    updated_user = result.scalar_one()

    assert updated_user.last_login is not None
    assert updated_user.last_login >= before_login

    after_login = datetime.now(timezone.utc).replace(tzinfo=None)

    assert updated_user.last_login <= after_login

async def test_failed_login_does_not_update_last_login(
    client: AsyncClient,
    viewer_user: User,
    db_session: AsyncSession,
) -> None:
    """Invalid credentials must not change the last login timestamp."""

    user_id = viewer_user.id

    # Establish the initial timestamp.
    initial_result = await db_session.execute(
        select(User.last_login).where(User.id == user_id)
    )
    initial_last_login = initial_result.scalar_one()

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": viewer_user.email,
            "password": "DefinitelyWrongPassword!",
        },
    )

    assert response.status_code == 401

    # Reload the value directly from the database.
    result = await db_session.execute(
        select(User.last_login).where(User.id == user_id)
    )

    assert result.scalar_one() == initial_last_login

async def test_repeated_login_updates_last_login(
    client: AsyncClient,
    viewer_user: User,
    db_session: AsyncSession,
) -> None:
    """Each successful login should update the last login timestamp."""

    user_id = viewer_user.id
    email = viewer_user.email

    credentials = {
        "email": email,
        "password": "TestPassword123!",
    }

    # First successful login.
    first_response = await client.post(
        "/api/v1/auth/login",
        json=credentials,
    )

    assert first_response.status_code == 200

    first_result = await db_session.execute(
        select(User.last_login).where(User.id == user_id)
    )

    first_login = first_result.scalar_one()

    assert first_login is not None

    # Second successful login.
    second_response = await client.post(
        "/api/v1/auth/login",
        json=credentials,
    )

    assert second_response.status_code == 200

    second_result = await db_session.execute(
        select(User.last_login).where(User.id == user_id)
    )

    second_login = second_result.scalar_one()

    assert second_login is not None
    assert second_login > first_login

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

async def test_protected_route_rejects_token_without_subject(
    client: AsyncClient,
) -> None:
    """A JWT without a subject must be rejected cleanly."""

    from app.core.security import create_access_token

    token = create_access_token(
        {
            "role": "viewer",
        }
    )

    response = await client.get(
        "/api/v1/events/",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"


async def test_protected_route_rejects_nonnumeric_subject(
    client: AsyncClient,
) -> None:
    """A malformed JWT subject must return 401 rather than causing a 500."""

    from app.core.security import create_access_token

    token = create_access_token(
        {
            "sub": "not-a-user-id",
            "role": "viewer",
        }
    )

    response = await client.get(
        "/api/v1/events/",
        headers={
            "Authorization": f"Bearer {token}",
        },
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid token"
"""Authentication and role-based access-control tests."""

from httpx import AsyncClient

from app.models.user import User


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


async def test_missing_token_is_rejected(
    client: AsyncClient,
) -> None:
    """A protected endpoint should reject an unauthenticated request."""

    response = await client.get(
        "/api/v1/auth/audit",
    )

    assert response.status_code == 401


async def test_admin_can_access_admin_endpoint(
    admin_client: AsyncClient,
) -> None:
    """Administrators should be allowed to access the audit endpoint."""

    response = await admin_client.get(
        "/api/v1/auth/audit",
    )

    assert response.status_code == 200


async def test_analyst_cannot_access_admin_endpoint(
    analyst_client: AsyncClient,
) -> None:
    """Analysts should not have administrator-only access."""

    response = await analyst_client.get(
        "/api/v1/auth/audit",
    )

    assert response.status_code == 403


async def test_viewer_cannot_access_admin_endpoint(
    viewer_client: AsyncClient,
) -> None:
    """Viewers should not have administrator-only access."""

    response = await viewer_client.get(
        "/api/v1/auth/audit",
    )

    assert response.status_code == 403

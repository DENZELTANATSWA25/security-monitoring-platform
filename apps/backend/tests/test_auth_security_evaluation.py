"""Phase 6A: negative authentication and RBAC security tests."""

from datetime import datetime, timedelta, timezone

import pytest
from jose import jwt
from sqlalchemy import delete

from app.core.config import settings
from app.models.user import User, UserRole


pytestmark = pytest.mark.asyncio


def make_token(subject, *, secret=None, expires_in_minutes=15, **claims):
    """Create a test JWT using the configured algorithm."""
    payload = {
        "sub": str(subject),
        "exp": datetime.now(timezone.utc)
        + timedelta(minutes=expires_in_minutes),
        **claims,
    }

    return jwt.encode(
        payload,
        secret if secret is not None else settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def authorization(token):
    """Construct a Bearer authorization header."""
    return {"Authorization": f"Bearer {token}"}


async def test_expired_token_is_rejected(client, viewer_user):
    token = make_token(viewer_user.id, expires_in_minutes=-10)

    response = await client.get(
        "/api/v1/users/me",
        headers=authorization(token),
    )

    assert response.status_code == 401


async def test_tampered_token_is_rejected(client, viewer_user):
    token = make_token(viewer_user.id)
    parts = token.split(".")

    # Alter the signature without changing the payload.
    signature = parts[2]
    replacement = "A" if signature[0] != "A" else "B"
    parts[2] = replacement + signature[1:]

    response = await client.get(
        "/api/v1/users/me",
        headers=authorization(".".join(parts)),
    )

    assert response.status_code == 401


async def test_malformed_token_is_rejected(client):
    response = await client.get(
        "/api/v1/users/me",
        headers=authorization("not-a-valid-jwt"),
    )

    assert response.status_code == 401


async def test_token_signed_with_wrong_secret_is_rejected(
    client,
    viewer_user,
):
    token = make_token(
        viewer_user.id,
        secret="incorrect-test-signing-key",
    )

    response = await client.get(
        "/api/v1/users/me",
        headers=authorization(token),
    )

    assert response.status_code == 401


async def test_deactivated_user_cannot_reuse_token(
    client,
    db_session,
    viewer_user,
):
    token = make_token(viewer_user.id)

    viewer_user.is_active = False
    await db_session.flush()

    response = await client.get(
        "/api/v1/users/me",
        headers=authorization(token),
    )

    assert response.status_code == 403


async def test_deleted_user_cannot_reuse_token(
    client,
    db_session,
    viewer_user,
):
    user_id = viewer_user.id
    token = make_token(user_id)

    await db_session.execute(
        delete(User).where(User.id == user_id)
    )
    await db_session.flush()

    response = await client.get(
        "/api/v1/users/me",
        headers=authorization(token),
    )

    # Existing application contract.
    assert response.status_code == 404


async def test_downgraded_admin_loses_admin_access(
    client,
    db_session,
    admin_user,
):
    token = make_token(admin_user.id)

    admin_user.role = UserRole.VIEWER
    await db_session.flush()

    response = await client.get(
        "/api/v1/users/",
        headers=authorization(token),
    )

    assert response.status_code == 403


async def test_forged_role_claim_does_not_escalate_privileges(
    client,
    viewer_user,
):
    # A correctly signed token containing an untrusted role claim
    # must not override the user's actual database role.
    token = make_token(viewer_user.id, role="admin")

    response = await client.get(
        "/api/v1/users/",
        headers=authorization(token),
    )

    assert response.status_code == 403

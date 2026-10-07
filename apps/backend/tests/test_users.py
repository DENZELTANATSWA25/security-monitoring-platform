"""Integration tests for the user-management API."""

import pytest
from httpx import AsyncClient


pytestmark = pytest.mark.asyncio


async def test_me_requires_authentication(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/v1/users/me")

    assert response.status_code == 401


async def test_authenticated_user_can_read_self(
    viewer_client: AsyncClient,
    viewer_user,
) -> None:
    response = await viewer_client.get("/api/v1/users/me")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == viewer_user.id
    assert data["email"] == viewer_user.email
    assert data["role"] == "viewer"


async def test_admin_can_list_users(
    admin_client: AsyncClient,
    admin_user,
) -> None:
    response = await admin_client.get("/api/v1/users/")

    assert response.status_code == 200

    users = response.json()

    assert any(
        user["id"] == admin_user.id
        for user in users
    )


async def test_viewer_cannot_list_users(
    viewer_client: AsyncClient,
) -> None:
    response = await viewer_client.get("/api/v1/users/")

    assert response.status_code == 403


async def test_admin_can_read_user(
    admin_client: AsyncClient,
    viewer_user,
) -> None:
    response = await admin_client.get(
        f"/api/v1/users/{viewer_user.id}"
    )

    assert response.status_code == 200
    assert response.json()["id"] == viewer_user.id


async def test_admin_gets_404_for_missing_user(
    admin_client: AsyncClient,
) -> None:
    response = await admin_client.get(
        "/api/v1/users/999999"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "User not found"


async def test_viewer_cannot_read_another_user(
    viewer_client: AsyncClient,
    admin_user,
) -> None:
    response = await viewer_client.get(
        f"/api/v1/users/{admin_user.id}"
    )

    assert response.status_code == 403


async def test_admin_and_analyst_can_list_assignable_users(
    admin_client: AsyncClient,
    analyst_client: AsyncClient,
) -> None:
    admin_response = await admin_client.get(
        "/api/v1/users/assignable"
    )
    analyst_response = await analyst_client.get(
        "/api/v1/users/assignable"
    )

    assert admin_response.status_code == 200
    assert analyst_response.status_code == 200


async def test_viewer_cannot_list_assignable_users(
    viewer_client: AsyncClient,
) -> None:
    response = await viewer_client.get(
        "/api/v1/users/assignable"
    )

    assert response.status_code == 403


async def test_assignable_users_exclude_viewers(
    admin_client: AsyncClient,
    viewer_user,
) -> None:
    response = await admin_client.get(
        "/api/v1/users/assignable"
    )

    assert response.status_code == 200

    ids = {
        user["id"]
        for user in response.json()
    }

    assert viewer_user.id not in ids


async def test_admin_can_change_user_role(
    admin_client: AsyncClient,
    viewer_user,
) -> None:
    response = await admin_client.patch(
        f"/api/v1/users/{viewer_user.id}/role",
        json={"role": "analyst"},
    )

    assert response.status_code == 200
    assert response.json()["role"] == "analyst"


async def test_viewer_cannot_change_user_role(
    viewer_client: AsyncClient,
    analyst_user,
) -> None:
    response = await viewer_client.patch(
        f"/api/v1/users/{analyst_user.id}/role",
        json={"role": "viewer"},
    )

    assert response.status_code == 403


async def test_admin_cannot_change_own_role(
    admin_client: AsyncClient,
    admin_user,
) -> None:
    response = await admin_client.patch(
        f"/api/v1/users/{admin_user.id}/role",
        json={"role": "viewer"},
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "You cannot change your own role"
    )


async def test_admin_can_deactivate_user(
    admin_client: AsyncClient,
    viewer_user,
) -> None:
    response = await admin_client.patch(
        f"/api/v1/users/{viewer_user.id}/status",
        json={"is_active": False},
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False


async def test_admin_cannot_deactivate_self(
    admin_client: AsyncClient,
    admin_user,
) -> None:
    response = await admin_client.patch(
        f"/api/v1/users/{admin_user.id}/status",
        json={"is_active": False},
    )

    assert response.status_code == 400
    assert (
        response.json()["detail"]
        == "You cannot deactivate your own account"
    )


async def test_viewer_cannot_change_user_status(
    viewer_client: AsyncClient,
    analyst_user,
) -> None:
    response = await viewer_client.patch(
        f"/api/v1/users/{analyst_user.id}/status",
        json={"is_active": False},
    )

    assert response.status_code == 403


async def test_admin_can_verify_user(
    admin_client: AsyncClient,
    viewer_user,
) -> None:
    response = await admin_client.patch(
        f"/api/v1/users/{viewer_user.id}/verification",
        json={"is_verified": True},
    )

    assert response.status_code == 200
    assert response.json()["is_verified"] is True


async def test_viewer_cannot_change_verification(
    viewer_client: AsyncClient,
    analyst_user,
) -> None:
    response = await viewer_client.patch(
        f"/api/v1/users/{analyst_user.id}/verification",
        json={"is_verified": True},
    )

    assert response.status_code == 403


async def test_user_mutations_return_404_for_missing_user(
    admin_client: AsyncClient,
) -> None:
    role_response = await admin_client.patch(
        "/api/v1/users/999999/role",
        json={"role": "analyst"},
    )

    status_response = await admin_client.patch(
        "/api/v1/users/999999/status",
        json={"is_active": False},
    )

    verification_response = await admin_client.patch(
        "/api/v1/users/999999/verification",
        json={"is_verified": True},
    )

    assert role_response.status_code == 404
    assert status_response.status_code == 404
    assert verification_response.status_code == 404

async def test_user_admin_mutations_create_audit_logs(
    admin_client: AsyncClient,
    admin_user,
    viewer_user,
    db_session,
) -> None:
    """Security-sensitive user administration must be auditable."""

    from sqlalchemy import select

    from app.models.audit_log import AuditLog

    role_response = await admin_client.patch(
        f"/api/v1/users/{viewer_user.id}/role",
        json={"role": "analyst"},
    )

    assert role_response.status_code == 200

    status_response = await admin_client.patch(
        f"/api/v1/users/{viewer_user.id}/status",
        json={"is_active": False},
    )

    assert status_response.status_code == 200

    verification_response = await admin_client.patch(
        f"/api/v1/users/{viewer_user.id}/verification",
        json={"is_verified": True},
    )

    assert verification_response.status_code == 200

    result = await db_session.execute(
        select(AuditLog)
        .where(
            AuditLog.user_id == admin_user.id,
            AuditLog.resource == "USER",
        )
    )

    audit_logs = result.scalars().all()

    actions = {
        audit_log.action
        for audit_log in audit_logs
    }

    assert "USER_ROLE_CHANGED" in actions
    assert "USER_STATUS_CHANGED" in actions
    assert "USER_VERIFICATION_CHANGED" in actions
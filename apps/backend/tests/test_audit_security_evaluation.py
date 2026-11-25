"""Phase 6E: audit attribution and authorization evaluation."""

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.user import User, UserRole

pytestmark = pytest.mark.asyncio


async def audit_records(
    db: AsyncSession,
    *,
    action: str,
) -> list[AuditLog]:
    """Retrieve audit records for one action."""
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.action == action)
        .order_by(AuditLog.id.asc())
    )
    return list(result.scalars().all())


async def audit_count(
    db: AsyncSession,
    *,
    action: str,
) -> int:
    """Count audit records without loading ORM objects."""
    result = await db.execute(
        select(func.count())
        .select_from(AuditLog)
        .where(AuditLog.action == action)
    )
    return result.scalar_one()


async def test_successful_login_records_correct_actor(
    analyst_client: AsyncClient,
    analyst_user: User,
    db_session: AsyncSession,
) -> None:
    """Successful authentication must identify the actual user."""

    records = await audit_records(
        db_session,
        action="LOGIN",
    )

    matching = [
        record
        for record in records
        if record.user_id == analyst_user.id
    ]

    assert len(matching) == 1
    assert matching[0].resource == "USER"
    assert analyst_user.email in (matching[0].details or "")


async def test_admin_role_change_has_correct_audit_actor(
    admin_client: AsyncClient,
    admin_user: User,
    analyst_user: User,
    db_session: AsyncSession,
) -> None:
    """Role-change audit must identify the administrator, not the target."""

    before = await audit_count(
        db_session,
        action="USER_ROLE_CHANGED",
    )

    response = await admin_client.patch(
        f"/api/v1/users/{analyst_user.id}/role",
        json={"role": UserRole.VIEWER.value},
    )

    assert response.status_code == 200

    records = await audit_records(
        db_session,
        action="USER_ROLE_CHANGED",
    )

    assert len(records) == before + 1

    record = records[-1]

    assert record.user_id == admin_user.id
    assert record.user_id != analyst_user.id
    assert record.resource == "USER"
    assert str(analyst_user.id) in (record.details or "")
    assert UserRole.VIEWER.value in (record.details or "")


async def test_viewer_role_change_is_rejected_without_audit_entry(
    viewer_client: AsyncClient,
    viewer_user: User,
    analyst_user: User,
    db_session: AsyncSession,
) -> None:
    """A rejected role change must not be logged as a completed change."""

    before = await audit_count(
        db_session,
        action="USER_ROLE_CHANGED",
    )

    response = await viewer_client.patch(
        f"/api/v1/users/{analyst_user.id}/role",
        json={"role": "ADMIN"},
    )

    assert response.status_code == 403

    after = await audit_count(
        db_session,
        action="USER_ROLE_CHANGED",
    )

    assert after == before


async def test_failed_login_has_no_success_audit_entry(
    client: AsyncClient,
    analyst_user: User,
    db_session: AsyncSession,
) -> None:
    """Rejected authentication must not be recorded as successful LOGIN."""

    before = await audit_count(
        db_session,
        action="LOGIN",
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": analyst_user.email,
            "password": "IncorrectPassword123!",
        },
    )

    assert response.status_code == 401

    after = await audit_count(
        db_session,
        action="LOGIN",
    )

    assert after == before


async def test_role_change_audit_failure_rolls_back_update(
    admin_client: AsyncClient,
    analyst_user: User,
    db_session: AsyncSession,
) -> None:
    """A failed audit write must not persist a role change."""
    from unittest.mock import patch

    original_role = analyst_user.role
    target_user_id = analyst_user.id

    async def fail_audit(*args, **kwargs):
        raise RuntimeError("Synthetic audit write failure")

    with patch(
        "app.api.v1.endpoints.users.log_event",
        side_effect=fail_audit,
    ):
        try:
            await admin_client.patch(
                f"/api/v1/users/{target_user_id}/role",
                json={"role": UserRole.VIEWER.value},
            )
        except RuntimeError as exc:
            assert "Synthetic audit write failure" in str(exc)
        else:
            pytest.fail("Expected the injected audit failure")

    # The route does not explicitly catch arbitrary audit failures.
    # Roll back the shared test session before querying the database.
    await db_session.rollback()

    result = await db_session.execute(
        select(User.role).where(User.id == target_user_id)
    )

    assert result.scalar_one() == original_role


async def test_telemetry_credential_not_exposed_in_audit_log(
    admin_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Generated telemetry credentials must not appear in audit details."""
    from uuid import uuid4

    # Unique name prevents collisions with existing test fixtures.
    source_name = f"audit-evaluation-{uuid4().hex[:12]}"

    create_response = await admin_client.post(
        "/api/v1/telemetry-sources",
        json={
            "name": source_name,
            "source_type": "APPLICATION",
        },
    )

    assert create_response.status_code == 201, create_response.text

    source_id = create_response.json()["id"]
    original_credential = create_response.json()["credential"]

    rotate_response = await admin_client.post(
        f"/api/v1/telemetry-sources/{source_id}/rotate-credential"
    )

    assert rotate_response.status_code == 200, rotate_response.text

    rotated_credential = rotate_response.json()["credential"]

    assert rotated_credential
    assert rotated_credential != original_credential

    result = await db_session.execute(
        select(AuditLog).where(
            AuditLog.action.in_(
                [
                    "TELEMETRY_SOURCE_CREATED",
                    "TELEMETRY_SOURCE_CREDENTIAL_ROTATED",
                ]
            )
        )
    )

    records = [
        record
        for record in result.scalars().all()
        if source_name in (record.details or "")
    ]

    assert len(records) == 2

    actions = {record.action for record in records}

    assert actions == {
        "TELEMETRY_SOURCE_CREATED",
        "TELEMETRY_SOURCE_CREDENTIAL_ROTATED",
    }

    for record in records:
        assert original_credential not in (record.details or "")
        assert rotated_credential not in (record.details or "")

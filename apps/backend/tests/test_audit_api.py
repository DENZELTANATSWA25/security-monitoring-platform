"""Tests for administrative audit-log access."""

from datetime import datetime, timedelta

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def _create_audit_log(
    db_session: AsyncSession,
    *,
    action: str,
    resource: str = "TEST_RESOURCE",
    details: str | None = None,
    timestamp: datetime | None = None,
) -> AuditLog:
    """Create and persist an audit log for an API test."""

    audit_log = AuditLog(
        action=action,
        resource=resource,
        details=details,
    )

    if timestamp is not None:
        audit_log.timestamp = timestamp

    db_session.add(audit_log)
    await db_session.commit()
    await db_session.refresh(audit_log)

    return audit_log


async def test_unauthenticated_user_cannot_list_audit_logs(
    client: AsyncClient,
) -> None:
    """Audit logs must require authentication."""

    response = await client.get(
        "/api/v1/audit",
    )

    assert response.status_code == 401


async def test_admin_can_list_audit_logs(
    admin_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Administrators should be able to inspect audit logs."""

    audit_log = await _create_audit_log(
        db_session,
        action="AUDIT_LIST_TEST",
        details="Audit API test entry.",
    )

    response = await admin_client.get(
        "/api/v1/audit",
    )

    assert response.status_code == 200

    matching_logs = [
        item
        for item in response.json()
        if item["id"] == audit_log.id
    ]

    assert len(matching_logs) == 1

    returned_log = matching_logs[0]

    assert returned_log["action"] == "AUDIT_LIST_TEST"
    assert returned_log["resource"] == "TEST_RESOURCE"
    assert returned_log["details"] == "Audit API test entry."


async def test_analyst_cannot_list_audit_logs(
    analyst_client: AsyncClient,
) -> None:
    """Analysts must not have administrator-only audit access."""

    response = await analyst_client.get(
        "/api/v1/audit",
    )

    assert response.status_code == 403


async def test_viewer_cannot_list_audit_logs(
    viewer_client: AsyncClient,
) -> None:
    """Viewers must not have administrator-only audit access."""

    response = await viewer_client.get(
        "/api/v1/audit",
    )

    assert response.status_code == 403


async def test_audit_logs_are_returned_newest_first(
    admin_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Audit logs should be returned in reverse chronological order."""

    now = datetime.utcnow()

    older_log = await _create_audit_log(
        db_session,
        action="OLDER_AUDIT_TEST",
        timestamp=now - timedelta(minutes=10),
    )

    newer_log = await _create_audit_log(
        db_session,
        action="NEWER_AUDIT_TEST",
        timestamp=now,
    )

    response = await admin_client.get(
        "/api/v1/audit",
    )

    assert response.status_code == 200

    returned_ids = [
        item["id"]
        for item in response.json()
    ]

    assert returned_ids.index(newer_log.id) < returned_ids.index(
        older_log.id
    )


async def test_audit_log_limit_is_applied(
    admin_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """The audit endpoint should respect the requested result limit."""

    for index in range(3):
        await _create_audit_log(
            db_session,
            action=f"LIMIT_AUDIT_TEST_{index}",
        )

    response = await admin_client.get(
        "/api/v1/audit",
        params={
            "limit": 2,
        },
    )

    assert response.status_code == 200
    assert len(response.json()) == 2


async def test_audit_log_offset_is_applied(
    admin_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """The audit endpoint should support result offsets."""

    now = datetime.utcnow()

    await _create_audit_log(
        db_session,
        action="OFFSET_NEWEST_TEST",
        timestamp=now,
    )

    await _create_audit_log(
        db_session,
        action="OFFSET_SECOND_TEST",
        timestamp=now - timedelta(minutes=1),
    )

    unpaginated_response = await admin_client.get(
        "/api/v1/audit",
        params={
            "limit": 100,
            "offset": 0,
        },
    )

    assert unpaginated_response.status_code == 200

    unpaginated_logs = unpaginated_response.json()

    assert len(unpaginated_logs) >= 2

    response = await admin_client.get(
        "/api/v1/audit",
        params={
            "limit": 1,
            "offset": 1,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert len(body) == 1
    assert body[0]["id"] == unpaginated_logs[1]["id"]


async def test_audit_log_limit_must_be_positive(
    admin_client: AsyncClient,
) -> None:
    """Audit-log limits below one should be rejected."""

    response = await admin_client.get(
        "/api/v1/audit",
        params={
            "limit": 0,
        },
    )

    assert response.status_code == 422


async def test_audit_log_limit_cannot_exceed_maximum(
    admin_client: AsyncClient,
) -> None:
    """Audit-log limits above the API maximum should be rejected."""

    response = await admin_client.get(
        "/api/v1/audit",
        params={
            "limit": 101,
        },
    )

    assert response.status_code == 422


async def test_audit_log_offset_cannot_be_negative(
    admin_client: AsyncClient,
) -> None:
    """Negative audit-log offsets should be rejected."""

    response = await admin_client.get(
        "/api/v1/audit",
        params={
            "offset": -1,
        },
    )

    assert response.status_code == 422

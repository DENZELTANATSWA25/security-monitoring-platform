"""Tests for the audit-log service layer."""

from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.services.audit_service import get_audit_logs, log_event


async def test_log_event_adds_audit_log_to_transaction(
    db_session: AsyncSession,
) -> None:
    """Logging an event should persist it within the current transaction."""

    event = await log_event(
        db=db_session,
        action="SERVICE_LOG_TEST",
        resource="TEST_RESOURCE",
        user_id=None,
        details="Service test audit entry.",
    )

    assert event.id is not None
    assert event.action == "SERVICE_LOG_TEST"
    assert event.resource == "TEST_RESOURCE"
    assert event.details == "Service test audit entry."


async def test_get_audit_logs_returns_newest_first(
    db_session: AsyncSession,
) -> None:
    """Audit retrieval should use reverse chronological ordering."""

    now = datetime.utcnow()

    older = AuditLog(
        action="SERVICE_OLDER_TEST",
        resource="TEST_RESOURCE",
        timestamp=now - timedelta(minutes=5),
    )

    newer = AuditLog(
        action="SERVICE_NEWER_TEST",
        resource="TEST_RESOURCE",
        timestamp=now,
    )

    db_session.add_all([
        older,
        newer,
    ])
    await db_session.flush()

    logs = await get_audit_logs(
        db_session,
        limit=100,
    )

    returned_ids = [
        log.id
        for log in logs
    ]

    assert returned_ids.index(newer.id) < returned_ids.index(older.id)


async def test_get_audit_logs_applies_limit_and_offset(
    db_session: AsyncSession,
) -> None:
    """Audit retrieval should apply pagination parameters."""

    now = datetime.utcnow()

    logs = [
        AuditLog(
            action=f"SERVICE_PAGE_TEST_{index}",
            resource="TEST_RESOURCE",
            timestamp=now - timedelta(minutes=index),
        )
        for index in range(3)
    ]

    db_session.add_all(logs)
    await db_session.flush()

    result = await get_audit_logs(
        db_session,
        limit=1,
        offset=1,
    )

    assert len(result) == 1
    assert result[0].id == logs[1].id

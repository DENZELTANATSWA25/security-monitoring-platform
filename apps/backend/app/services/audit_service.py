"""Service layer for application audit logging."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


async def log_event(
    db: AsyncSession,
    action: str,
    resource: str,
    user_id: int | None = None,
    details: str | None = None,
) -> AuditLog:
    """
    Add an audit event to the current database transaction.

    Transaction ownership belongs to the calling workflow. This allows the
    business operation and its audit record to succeed or fail atomically.
    """

    event = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        details=details,
    )

    db.add(event)
    await db.flush()

    return event


async def get_audit_logs(
    db: AsyncSession,
    *,
    limit: int = 50,
    offset: int = 0,
) -> list[AuditLog]:
    """Return audit logs in reverse chronological order."""

    result = await db.execute(
        select(AuditLog)
        .order_by(
            AuditLog.timestamp.desc(),
            AuditLog.id.desc(),
        )
        .offset(offset)
        .limit(limit)
    )

    return list(result.scalars().all())

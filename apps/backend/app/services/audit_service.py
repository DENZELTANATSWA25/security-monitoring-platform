"""Service layer for application audit logging."""

from datetime import datetime

from sqlalchemy import asc, desc, or_, select
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
    user_id: int | None = None,
    action: str | None = None,
    resource: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    search: str | None = None,
    sort_order: str = "desc",
) -> list[AuditLog]:
    """Return filtered and paginated audit logs."""

    query = select(AuditLog)

    if user_id is not None:
        query = query.where(
            AuditLog.user_id == user_id
        )

    if action is not None:
        query = query.where(
            AuditLog.action == action
        )

    if resource is not None:
        query = query.where(
            AuditLog.resource == resource
        )

    if start_date is not None:
        query = query.where(
            AuditLog.timestamp >= start_date
        )

    if end_date is not None:
        query = query.where(
            AuditLog.timestamp <= end_date
        )

    if search:
        search_term = f"%{search.strip()}%"

        query = query.where(
            or_(
                AuditLog.action.ilike(search_term),
                AuditLog.resource.ilike(search_term),
                AuditLog.details.ilike(search_term),
            )
        )

    order_function = (
        asc
        if sort_order == "asc"
        else desc
    )

    query = (
        query
        .order_by(
            order_function(AuditLog.timestamp),
            order_function(AuditLog.id),
        )
        .offset(offset)
        .limit(limit)
    )

    result = await db.execute(query)

    return list(result.scalars().all())
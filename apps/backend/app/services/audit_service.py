# Service layer for application audit logging.

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog

async def log_event(
        db: AsyncSession,
        action: str,
        resource: str,
        user_id: int | None = None,
        details: str | None = None
) -> AuditLog:
    """
    Add an audit event to the current database transaction.

    Transaction ownership belongs to the calling workflow. This allows the business operation and its audit record to succeed or fail atomically.
    """

    event = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        details=details
    )
    
    db.add(event)
    await db.flush()

    return event
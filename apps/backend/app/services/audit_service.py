from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog

async def log_event(
        db: AsyncSession,
        action: str,
        resource: str,
        user_id: int | None = None,
        details: str | None = None
):
    event = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        details=details
    )
    
    db.add(event)
    await db.commit()
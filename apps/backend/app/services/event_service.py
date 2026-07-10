from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from app.models.security_event import SecurityEvent
from app.schemas.security_event import SecurityEventCreate
from app.services.detection_service import detect_bruteforce



async def create_event(
    db: AsyncSession,
    event_data: SecurityEventCreate
):

    # prevent duplicate active brute-force events

    existing = await db.execute(
        select(SecurityEvent)
        .where(
            SecurityEvent.event_type == event_data.event_type,
            SecurityEvent.message == event_data.message
        )
    )

    duplicate = existing.scalar_one_or_none()


    if duplicate:
        return duplicate



    event = SecurityEvent(
        event_type=event_data.event_type,
        severity=event_data.severity,
        source=event_data.source,
        message=event_data.message,
        user_id=event_data.user_id
    )


    db.add(event)

    await db.commit()

    await db.refresh(event)

    await detect_bruteforce(db)

    return event
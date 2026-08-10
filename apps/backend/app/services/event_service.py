from sqlalchemy.ext.asyncio import AsyncSession

from sqlalchemy import select

from app.models.security_event import SecurityEvent
from app.schemas.security_event import SecurityEventCreate
from app.services.alert_service import create_alert
from app.services.detection.engine import run_detection

from app.core.websocket_manager import manager



async def create_event(
    db: AsyncSession,
    event_data: SecurityEventCreate
):

    # prevent duplicate active brute-force events

    existing = await db.execute(
        select(SecurityEvent)
        .where(
            SecurityEvent.event_type == event_data.event_type,
            SecurityEvent.message == event_data.description
        )
    )

    duplicate = existing.scalar_one_or_none()


    if duplicate:
        return duplicate

   
    #Create the event
    event = SecurityEvent(
        event_type=event_data.event_type,
        severity=event_data.severity,
        source=event_data.source,
        message=event_data.description,
        user_id=event_data.user_id,
        event_metadata=event_data.event_metadata
    )

    db.add(event)
    await db.commit()
    await db.refresh(event)

    #run the detection engine
    metadata = event_data.event_metadata or {}
    
    context = {
         "email": event_data.event_metadata.get("email"),
         "ip": event_data.event_metadata.get("ip"),
        "event": event
        }

    results = await run_detection(
         db,
        context
    )

    for result in results:
        await create_alert(
            db=db,
            alert_type=result["alert_type"],
            severity=result["severity"],
            message=result["message"]
        )

    await manager.broadcast(
        {
            "type": "security_event",
            "event": {
                "id": event.id,
                "event_type": event.event_type,
                "severity": event.severity.value,
                "source": event.source,
                "message": event.message,
                "created_at": event.created_at.isoformat(),
            }
        }
    )

    return event
        
        
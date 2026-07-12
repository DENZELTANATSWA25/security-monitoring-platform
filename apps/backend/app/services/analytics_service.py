from sqlalchemy import select, func

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security_event import SecurityEvent

async def get_event_trend(
    db: AsyncSession
):
    
    result = await db.execute(
        select(
            func.date(SecurityEvent.created_at),
            func.count(SecurityEvent.id)
        )
        .group_by(func.date(SecurityEvent.created_at))
        .order_by(func.date(SecurityEvent.created_at))
    )

    row = result.all()

    return [
        {
            "date": str(date),
            "count": count,
        }
        for date, count in row
    ]
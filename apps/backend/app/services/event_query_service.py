from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security_event import SecurityEvent

async def get_all_events(db: AsyncSession):
    result =  await db.execute(
        select(SecurityEvent)
        .order_by(SecurityEvent.created_at.desc())
    )   

    return result.scalars().all()
"""Query service for security events."""

from datetime import datetime

from sqlalchemy import asc, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security_event import EventSeverity, SecurityEvent

async def get_all_events(
    db: AsyncSession,
    *,
    limit: int = 50,
    offset: int = 0,
    severity: EventSeverity | None = None,
    event_type: str | None = None,
    source: str | None = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    search: str | None = None,
    sort_order: str = "desc",
) -> list[SecurityEvent]:
    """Return filtered and paginated security events."""

    query = select(SecurityEvent)

    if severity is not None:
        query = query.where(
            SecurityEvent.severity == severity
        )

    if event_type is not None:
        query = query.where(
            SecurityEvent.event_type == event_type
        )

    if source is not None:
        query = query.where(
            SecurityEvent.source == source
        )

    if start_date is not None:
        query = query.where(
            SecurityEvent.created_at >= start_date
        )

    if end_date is not None:
        query = query.where(
            SecurityEvent.created_at <= end_date
        )

    if search:
        search_term = f"%{search.strip()}%"

        query = query.where(
            or_(
                SecurityEvent.event_type.ilike(search_term),
                SecurityEvent.source.ilike(search_term),
                SecurityEvent.message.ilike(search_term),
            )
        )

    order_function = (
        asc
        if sort_order == "asc"
        else desc
    )

    query= (
        query
        .order_by(
            order_function(SecurityEvent.created_at),
            order_function(SecurityEvent.id),
        )
        .offset(offset)
        .limit(limit)
    )

    result =  await db.execute(query)

    return list(result.scalars().all())
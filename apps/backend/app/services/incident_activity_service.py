from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.incident_activity import (
    IncidentActivity,
    IncidentActivityType,
)

async def add_incident_activity(
    db: AsyncSession,
    *,
    incident_id: int,
    activity_type: IncidentActivityType,
    description: str,
    actor_user_id: int | None = None,
    old_value: str | None = None,
    new_value: str | None = None,
) -> IncidentActivity:
    """
    Add an activity record to the current database transaction.


    This function deliberately does not commit. The calling service owns the transaction so the incident change and its activity record succeed or fail together.
    """
    activity = IncidentActivity(
        incident_id=incident_id,
        actor_user_id=actor_user_id,
        activity_type=activity_type,
        description=description,
        old_value=old_value,
        new_value=new_value,
    )
    db.add(activity)

    # Flush so SQLAlchemy sends the INSERT and assigns the primary key while keeping the operation inside the caller's transaction.
    await db.flush()

    return activity

async def get_incident_activities(
    db: AsyncSession,
    incident_id: int,
) -> list[IncidentActivity]:
    """Return an incident's activity history in chronological order."""

    result = await db.execute(
        select(IncidentActivity)
        .options(selectinload(IncidentActivity.actor))
        .where(IncidentActivity.incident_id == incident_id)
        .order_by(IncidentActivity.created_at.asc())
    )

    return result.scalars().all()
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident import (
    Incident,
    IncidentStatus,
)

from app.models.user import User

async def create_incident(
        db: AsyncSession,
        title: str,
        description: str,
        severity: str,
        event_id: int | None,
):
    incident = Incident(
        title=title,
        description=description,
        severity=severity,
        event_id=event_id,
    )

    db.add(incident)
    await db.commit()
    await db.refresh(incident)
    return incident

async def get_incidents(
        db: AsyncSession,
):
    result = await db.execute(
        select(Incident)
        .order_by(Incident.created_at.desc())
    )

    return result.scalars().all()

async def get_incidents(
        db: AsyncSession,
):
    result = await db.execute(
        select(Incident)
        .order_by(Incident.created_at.desc())
    )

    return result.scalars().all()

async def get_incident(
        db: AsyncSession,
        incident_id: int,
):
    result = await db.execute(
        select(Incident)
        .where(Incident.id == incident_id)
    )

    return result.scalar_one_or_none()

async def assign_incident(
        db: AsyncSession,
        incident_id: int,
        user: User,
):
    incident = await get_incident(
        db,
        incident_id,
    )

    if not incident:
        return None

    incident.assigned_user_id = user.id

    incident.assigned_to = user.full_name
    incident.status = IncidentStatus.IN_PROGRESS

    await db.commit()
    await db.refresh(incident)
    return incident

async def update_status(
        db: AsyncSession,
        incident_id: int,
        status: IncidentStatus,
):
    incident = await get_incident(
        db,
        incident_id,
    )

    if not incident:
        return None

    incident.status = status

    await db.commit()
    await db.refresh(incident)

    return incident

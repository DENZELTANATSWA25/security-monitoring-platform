from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident import (
    Incident,
    IncidentStatus,
)
from app.models.incident_activity import IncidentActivityType
from app.models.user import User
from app.services.incident_activity_service import add_incident_activity


async def create_incident(
    db: AsyncSession,
    title: str,
    description: str,
    severity: str,
    event_id: int | None,
    actor_user_id: int,
) -> Incident:
    """
    Create an incident and its initial timeline entry atomically.
    """
    incident = Incident(
        title=title,
        description=description,
        severity=severity,
        event_id=event_id,
    )

    db.add(incident)

    # We need the generated incident ID before the activity can reference it.
    await db.flush()

    await add_incident_activity(
        db,
        incident_id=incident.id,
        actor_user_id=actor_user_id,
        activity_type=IncidentActivityType.INCIDENT_CREATED,
        description="Incident created.",
        new_value=IncidentStatus.OPEN.value,
    )

    await db.commit()
    await db.refresh(incident)

    return incident


async def get_incidents(
    db: AsyncSession,
) -> list[Incident]:
    """
    Return incidents ordered from newest to oldest.
    """
    result = await db.execute(
        select(Incident)
        .order_by(
            Incident.created_at.desc(),
        )
    )

    return list(result.scalars().all())


async def get_incident(
    db: AsyncSession,
    incident_id: int,
) -> Incident | None:
    """
    Return a single incident by ID.
    """
    result = await db.execute(
        select(Incident)
        .where(
            Incident.id == incident_id,
        )
    )

    return result.scalar_one_or_none()


async def assign_incident(
    db: AsyncSession,
    incident_id: int,
    user: User,
    actor_user_id: int,
) -> Incident | None:
    """
    Assign an incident to an analyst/admin and record the assignment.

    Assignment moves an open incident into IN_PROGRESS.
    """
    incident = await get_incident(
        db,
        incident_id,
    )

    if not incident:
        return None

    previous_assignee = incident.assigned_to
    previous_status = incident.status

    incident.assigned_user_id = user.id
    incident.assigned_to = user.full_name

    await add_incident_activity(
        db,
        incident_id=incident.id,
        actor_user_id=actor_user_id,
        activity_type=IncidentActivityType.ASSIGNED,
        description=f"Incident assigned to {user.full_name}.",
        old_value=previous_assignee or "Unassigned",
        new_value=user.full_name,
    )

    if previous_status != IncidentStatus.IN_PROGRESS:
        incident.status = IncidentStatus.IN_PROGRESS

        await add_incident_activity(
            db,
            incident_id=incident.id,
            actor_user_id=actor_user_id,
            activity_type=IncidentActivityType.STATUS_CHANGED,
            description=(
                f"Incident status changed from "
                f"{previous_status.value} to "
                f"{IncidentStatus.IN_PROGRESS.value}."
            ),
            old_value=previous_status.value,
            new_value=IncidentStatus.IN_PROGRESS.value,
        )

    await db.commit()
    await db.refresh(incident)

    return incident


async def update_status(
    db: AsyncSession,
    incident_id: int,
    status: IncidentStatus,
    actor_user_id: int,
) -> Incident | None:
    """
    Change an incident's status and record the transition.
    """
    incident = await get_incident(
        db,
        incident_id,
    )

    if not incident:
        return None

    previous_status = incident.status

    # Avoid creating misleading duplicate timeline entries for no-op updates.
    if previous_status == status:
        return incident

    incident.status = status

    await add_incident_activity(
        db,
        incident_id=incident.id,
        actor_user_id=actor_user_id,
        activity_type=IncidentActivityType.STATUS_CHANGED,
        description=(
            f"Incident status changed from "
            f"{previous_status.value} to {status.value}."
        ),
        old_value=previous_status.value,
        new_value=status.value,
    )

    await db.commit()
    await db.refresh(incident)

    return incident
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.incident import (
    Incident,
    IncidentStatus,
)
from app.models.incident_activity import IncidentActivityType
from app.models.incident_resolution import IncidentResolution
from app.models.user import User
from app.services.incident_activity_service import add_incident_activity


class InvalidIncidentStatusTransitionError(Exception):
    """Raised when an incident status transition violates the lifecycle."""

    def __init__(
        self,
        current_status: IncidentStatus,
        requested_status: IncidentStatus,
    ) -> None:
        self.current_status = current_status
        self.requested_status = requested_status

        super().__init__(
            f"Incident cannot transition from "
            f"{current_status.value} to {requested_status.value}"
        )


class IncidentResolutionRequiredError(Exception):
    """Raised when resolving an incident without a documented resolution."""

    def __init__(self) -> None:
        super().__init__(
            "Incident resolution required before resolving incident"
        )


# Explicit lifecycle transitions.
#
# A resolved or closed incident may be explicitly reopened by moving it
# back to IN_PROGRESS. Assignment itself does not perform that transition.
ALLOWED_STATUS_TRANSITIONS: dict[
    IncidentStatus,
    set[IncidentStatus],
] = {
    IncidentStatus.OPEN: {
        IncidentStatus.IN_PROGRESS,
        IncidentStatus.RESOLVED,
    },
    IncidentStatus.IN_PROGRESS: {
        IncidentStatus.OPEN,
        IncidentStatus.RESOLVED,
    },
    IncidentStatus.RESOLVED: {
        IncidentStatus.IN_PROGRESS,
        IncidentStatus.CLOSED,
    },
    IncidentStatus.CLOSED: {
        IncidentStatus.IN_PROGRESS,
    },
}


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

    # The generated incident ID is required by the activity record.
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
    """Return incidents ordered from newest to oldest."""

    result = await db.execute(
        select(Incident).order_by(
            Incident.created_at.desc(),
        )
    )

    return list(result.scalars().all())


async def get_incident(
    db: AsyncSession,
    incident_id: int,
) -> Incident | None:
    """Return a single incident by ID."""

    result = await db.execute(
        select(Incident).where(
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
    Assign an incident to an analyst or administrator.

    Assignment automatically starts an OPEN incident by moving it to
    IN_PROGRESS.

    Reassigning an IN_PROGRESS, RESOLVED, or CLOSED incident does not
    implicitly change its lifecycle state. Reopening must be an explicit
    status transition.
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

    # Assignment starts a new OPEN investigation, but it must never
    # implicitly reopen an already resolved or closed investigation.
    if previous_status == IncidentStatus.OPEN:
        incident.status = IncidentStatus.IN_PROGRESS

        await add_incident_activity(
            db,
            incident_id=incident.id,
            actor_user_id=actor_user_id,
            activity_type=IncidentActivityType.STATUS_CHANGED,
            description=(
                f"Incident status changed from "
                f"{IncidentStatus.OPEN.value} to "
                f"{IncidentStatus.IN_PROGRESS.value}."
            ),
            old_value=IncidentStatus.OPEN.value,
            new_value=IncidentStatus.IN_PROGRESS.value,
        )

    await db.commit()
    await db.refresh(incident)

    return incident


async def _incident_has_resolution(
    db: AsyncSession,
    incident_id: int,
) -> bool:
    """Return whether an incident has a documented resolution."""

    result = await db.execute(
        select(IncidentResolution.id)
        .where(
            IncidentResolution.incident_id == incident_id,
        )
        .limit(1)
    )

    return result.scalar_one_or_none() is not None


async def update_status(
    db: AsyncSession,
    incident_id: int,
    status: IncidentStatus,
    actor_user_id: int,
) -> Incident | None:
    """
    Change an incident's status while enforcing its lifecycle.

    Resolving an incident requires a documented resolution.
    Closing is only permitted from RESOLVED.
    Reopening RESOLVED or CLOSED incidents must be explicit.
    """
    incident = await get_incident(
        db,
        incident_id,
    )

    if not incident:
        return None

    previous_status = incident.status

    # A request for the current state is idempotent and does not create
    # misleading timeline activity.
    if previous_status == status:
        return incident

    allowed_transitions = ALLOWED_STATUS_TRANSITIONS.get(
        previous_status,
        set(),
    )

    if status not in allowed_transitions:
        raise InvalidIncidentStatusTransitionError(
            current_status=previous_status,
            requested_status=status,
        )

    if status == IncidentStatus.RESOLVED:
        has_resolution = await _incident_has_resolution(
            db,
            incident.id,
        )

        if not has_resolution:
            raise IncidentResolutionRequiredError()

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
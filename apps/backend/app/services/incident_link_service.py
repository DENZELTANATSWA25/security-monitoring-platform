"""Services for linking investigation events and alerts to incidents."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.alert import Alert
from app.models.incident_activity import IncidentActivityType
from app.models.incident_alert_link import IncidentAlertLink
from app.models.incident_event_link import IncidentEventLink
from app.models.security_event import SecurityEvent
from app.services.incident_activity_service import add_incident_activity


class IncidentEventAlreadyLinkedError(Exception):
    """Raised when an event is already linked to an incident."""


class IncidentAlertAlreadyLinkedError(Exception):
    """Raised when an alert is already linked to an incident."""


async def get_incident_event_links(
    db: AsyncSession,
    incident_id: int,
) -> list[IncidentEventLink]:
    """Return additional security events linked to an incident."""

    result = await db.execute(
        select(IncidentEventLink)
        .options(
            selectinload(IncidentEventLink.event),
            selectinload(IncidentEventLink.linked_by),
        )
        .where(IncidentEventLink.incident_id == incident_id)
        .order_by(
            IncidentEventLink.created_at.asc(),
            IncidentEventLink.id.asc(),
        )
    )

    return list(result.scalars().all())


async def get_incident_alert_links(
    db: AsyncSession,
    incident_id: int,
) -> list[IncidentAlertLink]:
    """Return alerts linked to an incident."""

    result = await db.execute(
        select(IncidentAlertLink)
        .options(
            selectinload(IncidentAlertLink.alert),
            selectinload(IncidentAlertLink.linked_by),
        )
        .where(IncidentAlertLink.incident_id == incident_id)
        .order_by(
            IncidentAlertLink.created_at.asc(),
            IncidentAlertLink.id.asc(),
        )
    )

    return list(result.scalars().all())


async def link_event_to_incident(
    db: AsyncSession,
    *,
    incident_id: int,
    event_id: int,
    actor_user_id: int,
) -> IncidentEventLink | None:
    """
    Link an additional security event to an incident.

    Returns None when the requested security event does not exist.

    The link and its timeline activity are committed atomically. The database
    unique constraint is also treated as the final duplicate guard so that
    concurrent requests cannot create duplicate links.
    """

    event_result = await db.execute(
        select(SecurityEvent).where(SecurityEvent.id == event_id)
    )
    event = event_result.scalar_one_or_none()

    if event is None:
        return None

    link = IncidentEventLink(
        incident_id=incident_id,
        event_id=event_id,
        linked_by_user_id=actor_user_id,
    )

    db.add(link)

    try:
        # Flush first so database constraints are checked before the timeline
        # activity is created.
        await db.flush()

    except IntegrityError:
        # A failed flush leaves the transaction unusable until rollback.
        await db.rollback()

        # Re-check after rollback. If the link now exists, another request won
        # the race and this is a duplicate-link conflict.
        if await incident_event_link_exists(
            db=db,
            incident_id=incident_id,
            event_id=event_id,
        ):
            raise IncidentEventAlreadyLinkedError from None

        # The integrity failure was unrelated to the duplicate-link constraint.
        raise

    await add_incident_activity(
        db=db,
        incident_id=incident_id,
        actor_user_id=actor_user_id,
        activity_type=IncidentActivityType.EVENT_LINKED,
        description=f"Security event #{event.id} linked to incident.",
        new_value=f"Event #{event.id}",
    )

    # Commit the link and timeline entry as one transaction.
    await db.commit()

    # Query by the newly created link's primary key. Querying only by
    # incident_id would fail once an incident has multiple linked events.
    result = await db.execute(
        select(IncidentEventLink)
        .options(
            selectinload(IncidentEventLink.event),
            selectinload(IncidentEventLink.linked_by),
        )
        .where(IncidentEventLink.id == link.id)
    )

    return result.scalar_one()


async def link_alert_to_incident(
    db: AsyncSession,
    *,
    incident_id: int,
    alert_id: int,
    actor_user_id: int,
) -> IncidentAlertLink | None:
    """
    Link an alert to an incident.

    Returns None when the requested alert does not exist.

    The link and its timeline activity are committed atomically. The database
    unique constraint is also treated as the final duplicate guard so that
    concurrent requests cannot create duplicate links.
    """

    alert_result = await db.execute(
        select(Alert).where(Alert.id == alert_id)
    )
    alert = alert_result.scalar_one_or_none()

    if alert is None:
        return None

    link = IncidentAlertLink(
        incident_id=incident_id,
        alert_id=alert_id,
        linked_by_user_id=actor_user_id,
    )

    db.add(link)

    try:
        # Flush first so database constraints are checked before the timeline
        # activity is created.
        await db.flush()

    except IntegrityError:
        await db.rollback()

        if await incident_alert_link_exists(
            db=db,
            incident_id=incident_id,
            alert_id=alert_id,
        ):
            raise IncidentAlertAlreadyLinkedError from None

        # Preserve unrelated database integrity failures.
        raise

    await add_incident_activity(
        db=db,
        incident_id=incident_id,
        actor_user_id=actor_user_id,
        activity_type=IncidentActivityType.ALERT_LINKED,
        description=f"Alert #{alert.id} linked to incident.",
        new_value=f"Alert #{alert.id}",
    )

    await db.commit()

    # Query by the newly created link's primary key so multiple linked alerts
    # can coexist safely on the same incident.
    result = await db.execute(
        select(IncidentAlertLink)
        .options(
            selectinload(IncidentAlertLink.alert),
            selectinload(IncidentAlertLink.linked_by),
        )
        .where(IncidentAlertLink.id == link.id)
    )

    return result.scalar_one()


async def incident_event_link_exists(
    db: AsyncSession,
    *,
    incident_id: int,
    event_id: int,
) -> bool:
    """Return whether an event is already linked to an incident."""

    result = await db.execute(
        select(IncidentEventLink.id).where(
            IncidentEventLink.incident_id == incident_id,
            IncidentEventLink.event_id == event_id,
        )
    )

    return result.scalar_one_or_none() is not None


async def incident_alert_link_exists(
    db: AsyncSession,
    *,
    incident_id: int,
    alert_id: int,
) -> bool:
    """Return whether an alert is already linked to an incident."""

    result = await db.execute(
        select(IncidentAlertLink.id).where(
            IncidentAlertLink.incident_id == incident_id,
            IncidentAlertLink.alert_id == alert_id,
        )
    )

    return result.scalar_one_or_none() is not None
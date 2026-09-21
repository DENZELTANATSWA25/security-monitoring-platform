from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.incident_activity import IncidentActivityType
from app.models.incident_resolution import IncidentResolution
from app.schemas.incident_resolution import IncidentResolutionUpsert
from app.services.incident_activity_service import add_incident_activity


async def get_incident_resolution(
    db: AsyncSession,
    incident_id: int,
) -> IncidentResolution | None:
    """Return the current resolution for an incident, if one exists."""

    result = await db.execute(
        select(IncidentResolution)
        .options(
            selectinload(IncidentResolution.resolved_by),
        )
        .where(
            IncidentResolution.incident_id == incident_id,
        )
    )

    return result.scalar_one_or_none()


async def upsert_incident_resolution(
    db: AsyncSession,
    *,
    incident_id: int,
    resolution_data: IncidentResolutionUpsert,
    actor_user_id: int,
) -> IncidentResolution:
    """
    Create or update an incident's investigation resolution.

    Resolution changes and their corresponding incident activity are
    committed in one transaction.

    If the submitted resolution is identical to the stored resolution,
    no database update or audit activity is created.
    """

    result = await db.execute(
        select(IncidentResolution).where(
            IncidentResolution.incident_id == incident_id,
        )
    )

    resolution = result.scalar_one_or_none()

    if resolution is None:
        resolution = IncidentResolution(
            incident_id=incident_id,
            classification=resolution_data.classification,
            summary=resolution_data.summary,
            root_cause=resolution_data.root_cause,
            remediation=resolution_data.remediation,
            resolved_by_user_id=actor_user_id,
        )

        db.add(resolution)
        await db.flush()

        await add_incident_activity(
            db,
            incident_id=incident_id,
            activity_type=IncidentActivityType.RESOLUTION_ADDED,
            description="Incident resolution added.",
            actor_user_id=actor_user_id,
            new_value=resolution_data.classification.value,
        )

        await db.commit()

    else:
        has_changes = any(
            (
                resolution.classification
                != resolution_data.classification,

                resolution.summary
                != resolution_data.summary,

                resolution.root_cause
                != resolution_data.root_cause,

                resolution.remediation
                != resolution_data.remediation,
            )
        )

        if has_changes:
            previous_classification = (
                resolution.classification
            )

            resolution.classification = (
                resolution_data.classification
            )
            resolution.summary = (
                resolution_data.summary
            )
            resolution.root_cause = (
                resolution_data.root_cause
            )
            resolution.remediation = (
                resolution_data.remediation
            )
            resolution.resolved_by_user_id = (
                actor_user_id
            )

            await db.flush()

            await add_incident_activity(
                db,
                incident_id=incident_id,
                activity_type=(
                    IncidentActivityType.RESOLUTION_UPDATED
                ),
                description="Incident resolution updated.",
                actor_user_id=actor_user_id,
                old_value=previous_classification.value,
                new_value=resolution_data.classification.value,
            )

            await db.commit()

    result = await db.execute(
        select(IncidentResolution)
        .options(
            selectinload(IncidentResolution.resolved_by),
        )
        .where(
            IncidentResolution.id == resolution.id,
        )
    )

    return result.scalar_one()
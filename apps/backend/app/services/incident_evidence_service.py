from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.incident_activity import IncidentActivityType
from app.models.incident_evidence import (
    EvidenceType,
    IncidentEvidence,
)
from app.services.incident_activity_service import (
    add_incident_activity,
)

async def create_incident_evidence(
    db: AsyncSession,
    *,
    incident_id: int,
    evidence_type: EvidenceType,
    value: str,
    added_by_user_id: int,
    description: str | None = None,
    source: str | None = None,
) -> IncidentEvidence:
    """
    Add evidence to an incident and record the action in its timeline.

    The evidence row and activity entry are committed as one transaction.
    """

    evidence = IncidentEvidence(
        incident_id=incident_id,
        evidence_type=evidence_type,
        value=value,
        description=description,
        source=source,
        added_by_user_id=added_by_user_id,
    )

    db.add(evidence)

    # Generate the evidence ID without committing the transaction.
    await db.flush()

    await add_incident_activity(
        db,
        incident_id=incident_id,
        actor_user_id=added_by_user_id,
        activity_type=IncidentActivityType.EVIDENCE_ADDED,
        description="Evidence added to incident.",
        new_value=(
            f"{evidence_type.value}: {value}"
        ),
    )

    # Evidence and timeline activity succeed or fail together.
    await db.commit()

    # Reload with the author relationship eagerly loaded so Pydantic
    # serialization cannot trigger an asynchronous lazy-load operation.
    result = await db.execute(
        select(IncidentEvidence)
        .options(
            selectinload(IncidentEvidence.added_by),
        )
        .where(
            IncidentEvidence.id == evidence.id,
        )
    )

    return result.scalar_one()

async def get_incident_evidence(
    db: AsyncSession,
    incident_id: int,
) -> list[IncidentEvidence]:
    """
    Return evidence for an incident in chronological order.

    Evidence authors are eager-loaded to avoid N+1 queries and async relationship-loadeing problems during API serialization.
    """

    result = await db.execute(
        select(IncidentEvidence)
        .options(
            selectinload(IncidentEvidence.added_by),
        )
        .where(
            IncidentEvidence.incident_id == incident_id,
        )
        .order_by(
            IncidentEvidence.created_at.asc(),
            IncidentEvidence.id.asc(),
        )
    )

    return list(result.scalars().all())
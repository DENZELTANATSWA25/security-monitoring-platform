from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
from fastapi import status as http_status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.permissions import require_role
from app.db.session import get_db
from app.models.incident import IncidentStatus
from app.models.user import User, UserRole
from app.schemas.incident import (
    IncidentAssign,
    IncidentCreate,
    IncidentResponse,
)
from app.schemas.incident_link import (
    IncidentAlertLinkResponse,
    IncidentEventLinkResponse,
)

from app.schemas.incident_activity import IncidentActivityResponse
from app.schemas.incident_note import (
    IncidentNoteCreate,
    IncidentNoteResponse,
)
from app.schemas.incident_resolution import (
    IncidentResolutionResponse,
    IncidentResolutionUpsert,
)
from app.services.incident_resolution_service import (
    get_incident_resolution,
    upsert_incident_resolution,
)

from app.schemas.incident_evidence import (
    IncidentEvidenceCreate,
    IncidentEvidenceResponse,
)

from app.services.incident_activity_service import get_incident_activities
from app.services.incident_note_service import (
    create_incident_note,
    get_incident_notes,
)
from app.services.incident_service import (
    IncidentResolutionRequiredError,
    InvalidIncidentStatusTransitionError,
    assign_incident,
    create_incident,
    get_incident,
    get_incidents,
    update_status,
)
from app.services.incident_link_service import (
    IncidentAlertAlreadyLinkedError,
    IncidentEventAlreadyLinkedError,
    get_incident_alert_links,
    get_incident_event_links,
    incident_alert_link_exists,
    incident_event_link_exists,
    link_alert_to_incident,
    link_event_to_incident,
)

from app.services.incident_evidence_service import (
    create_incident_evidence,
    get_incident_evidence,
)
from app.services.user_service import get_user_by_id



router = APIRouter(
    prefix="/incidents",
    tags=["Incidents"],
)


@router.post(
    "/",
    response_model=IncidentResponse,
)
async def create(
    incident: IncidentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.ADMIN,
            UserRole.ANALYST,
        )
    ),
):
    """
    Create a new incident.

    The authenticated administrator or analyst is recorded as the actor
    responsible for creating the incident.
    """
    return await create_incident(
        db=db,
        title=incident.title,
        description=incident.description,
        severity=incident.severity,
        event_id=incident.event_id,
        actor_user_id=current_user.id,
    )


@router.get(
    "/",
    response_model=list[IncidentResponse],
)
async def list_incidents(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return all incidents."""
    return await get_incidents(db)


@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
)
async def read_incident(
    incident_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return a single incident."""
    incident = await get_incident(
        db,
        incident_id,
    )

    if not incident:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    return incident


@router.patch(
    "/{incident_id}/assign",
    response_model=IncidentResponse,
)
async def assign(
    incident_id: int,
    assignment: IncidentAssign,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.ADMIN,
            UserRole.ANALYST,
        )
    ),
):
    """
    Assign an incident to an active administrator or analyst.

    The authenticated user performing the assignment is recorded separately
    from the user receiving the assignment.
    """
    target_user = await get_user_by_id(
        db,
        assignment.user_id,
    )

    if not target_user:
        raise HTTPException(
            status_code=404,
            detail="Assigned user not found",
        )

    if not target_user.is_active:
        raise HTTPException(
            status_code=400,
            detail="Inactive users cannot be assigned to incidents",
        )

    if target_user.role not in (
        UserRole.ADMIN,
        UserRole.ANALYST,
    ):
        raise HTTPException(
            status_code=400,
            detail="Only administrators or analysts can be assigned to incidents",
        )

    incident = await assign_incident(
        db=db,
        incident_id=incident_id,
        user=target_user,
        actor_user_id=current_user.id,
    )

    if not incident:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    return incident


@router.patch(
    "/{incident_id}/status/{status}",
    response_model=IncidentResponse,
)

async def status(
    incident_id: int,
    status: IncidentStatus,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.ADMIN,
            UserRole.ANALYST,
        )
    ),
):
    """
    Change an incident's lifecycle status.

    Invalid lifecycle transitions are rejected. A documented resolution
    must exist before an incident can transition to RESOLVED.
    """
    try:
        incident = await update_status(
            db=db,
            incident_id=incident_id,
            status=status,
            actor_user_id=current_user.id,
        )

    except IncidentResolutionRequiredError as exc:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    except InvalidIncidentStatusTransitionError as exc:
        raise HTTPException(
            status_code=http_status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    if not incident:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    return incident


@router.post(
    "/{incident_id}/notes",
    response_model=IncidentNoteResponse,
)
async def create_note(
    incident_id: int,
    note: IncidentNoteCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.ADMIN,
            UserRole.ANALYST,
        )
    ),
):
    """
    Add an investigation note to an incident.

    The authenticated administrator or analyst is automatically recorded as
    both the note author and the actor responsible for the timeline event.
    """
    incident = await get_incident(
        db,
        incident_id,
    )

    if not incident:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    content = note.content.strip()

    if not content:
        raise HTTPException(
            status_code=400,
            detail="Note content cannot be empty",
        )

    return await create_incident_note(
        db=db,
        incident_id=incident_id,
        author_user_id=current_user.id,
        content=content,
    )


@router.get(
    "/{incident_id}/notes",
    response_model=list[IncidentNoteResponse],
)
async def list_notes(
    incident_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return investigation notes for an incident."""
    incident = await get_incident(
        db,
        incident_id,
    )

    if not incident:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    return await get_incident_notes(
        db,
        incident_id,
    )


@router.get(
    "/{incident_id}/activities",
    response_model=list[IncidentActivityResponse],
)
async def list_activities(
    incident_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Return the operational activity timeline for an incident.

    Activities are returned chronologically with actor information
    eager-loaded for API serialization.
    """
    incident = await get_incident(
        db,
        incident_id,
    )

    if not incident:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    return await get_incident_activities(
        db=db,
        incident_id=incident_id,
    )

@router.get(
    "/{incident_id}/events",
    response_model=list[IncidentEventLinkResponse],
)
async def list_linked_events(
    incident_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Return additional security events linked to an incident.

    The incident's originating event is stored separately in the Incident.event_id.
    This endpoint returns events linked later during investigation.
    """
    incident = await get_incident(
        db,
        incident_id,
    )

    if not incident:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    return await get_incident_event_links(
        db=db,
        incident_id=incident_id,
    )

@router.post(
    "/{incident_id}/events/{event_id}",
    response_model=IncidentEventLinkResponse,
    status_code=201,
)
async def link_event(
    incident_id: int,
    event_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.ADMIN,
            UserRole.ANALYST,
        )
    ),
):
    """
    Link an additional security event to an incident.

    The linkage and its incident timeline activity are committed as one database transaction.
    """
    incident = await get_incident(
        db,
        incident_id,
    )

    if not incident:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    # The originating event is already directly associated with the incident.
    # It must not also be duplicated in the additional-event linkage table.
    if incident.event_id == event_id:
        raise HTTPException(
            status_code=409,
            detail="Event is already the originating event for this incident.",
        )

    if await incident_event_link_exists(
        db=db,
        incident_id=incident_id,
        event_id=event_id,
    ):
        raise HTTPException(
            status_code=409,
            detail="Event is already linked to this incident.",
        )

    try:
        link = await link_event_to_incident(
            db=db,
            incident_id=incident_id,
            event_id=event_id,
            actor_user_id=current_user.id
        )
    except IncidentEventAlreadyLinkedError:
        raise HTTPException(
            status_code=409,
            detail="Event is already linked to this incident.",
        )

    if link is None:
        raise HTTPException(
            status_code=404,
            detail="Security event not found.",
        )

    return link

@router.get(
    "/{incident_id}/alerts",
    response_model=list[IncidentAlertLinkResponse],
)
async def list_linked_alerts(
    incident_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    # Return alerts linked to an incident investigation.
    incident = await get_incident(
        db,
        incident_id,
    )

    if not incident:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    return await get_incident_alert_links(
        db=db,
        incident_id=incident_id,
    )

@router.post(
    "/{incident_id}/alerts/{alert_id}",
    response_model=IncidentAlertLinkResponse,
    status_code=201,
)
async def link_alert(
    incident_id: int,
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.ADMIN,
            UserRole.ANALYST,
        )
    ),
):
    """
    Link an alert to an incident investigation.

    The linkage and its incident timeline activity are committed as one database transaction.
    """
    incident = await get_incident(
        db,
        incident_id,
    )

    if not incident:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    if await incident_alert_link_exists(
        db=db,
        incident_id=incident_id,
        alert_id=alert_id,
    ):
        raise HTTPException(
            status_code=409,
            detail="Alert is already linked to this incident.",
        )

    try:
        link = await link_alert_to_incident(
            db=db,
            incident_id=incident_id,
            alert_id=alert_id,
            actor_user_id=current_user.id,
        )
    except IncidentAlertAlreadyLinkedError:
        raise HTTPException(
            status_code=409,
            detail="Alert is already linked to this incident."
        )

    if link is None:
        raise HTTPException(
            status_code=404,
            detail="Alert not found.",
        )

    return link

@router.get(
    "/{incident_id}/evidence",
    response_model=list[IncidentEvidenceResponse],
)
async def list_evidence(
    incident_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """
    Return investigation evidence associated with an incident.

    All authenticated users may inspect evidence.
    """
    incident = await get_incident(
        db,
        incident_id,
    )

    if not incident:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    return await get_incident_evidence(
        db=db,
        incident_id=incident_id,
    )

@router.post(
    "/{incident_id}/evidence",
    response_model=IncidentEvidenceResponse,
    status_code=201,
)
async def add_evidence(
    incident_id: int,
    evidence: IncidentEvidenceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.ADMIN,
            UserRole.ANALYST,
        )
    ),
):
    """
    Add evidence to an incident investigation.

    The authenticated administrator or analyst is recorded as the evidence author and as the actor in the incident activity timeline.
    """
    incident = await get_incident(
        db,
        incident_id,
    )

    if not incident:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    return await create_incident_evidence(
        db=db,
        incident_id=incident_id,
        evidence_type=evidence.evidence_type,
        value=evidence.value,
        description=evidence.description,
        source=evidence.source,
        added_by_user_id=current_user.id,
    )

@router.get(
    "/{incident_id}/resolution",
    response_model=IncidentResolutionResponse,
)
async def read_incident_resolution(
    incident_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> IncidentResolutionResponse:
    """Return the current investigation resolution for an incident."""

    incident = await get_incident(
        db,
        incident_id,
    )

    if incident is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    resolution = await get_incident_resolution(
        db,
        incident_id,
    )

    if resolution is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Incident resolution not found",
        )

    return resolution


@router.put(
    "/{incident_id}/resolution",
    response_model=IncidentResolutionResponse,
)
async def put_incident_resolution(
    incident_id: int,
    resolution_data: IncidentResolutionUpsert,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(
            UserRole.ADMIN,
            UserRole.ANALYST,
        )
    ),
) -> IncidentResolutionResponse:
    """Create or update the investigation resolution for an incident."""

    incident = await get_incident(
        db,
        incident_id,
    )

    if incident is None:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND,
            detail="Incident not found",
        )

    return await upsert_incident_resolution(
        db,
        incident_id=incident_id,
        resolution_data=resolution_data,
        actor_user_id=current_user.id,
    )
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)
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
from app.schemas.incident_activity import IncidentActivityResponse
from app.schemas.incident_note import (
    IncidentNoteCreate,
    IncidentNoteResponse,
)
from app.services.incident_activity_service import get_incident_activities
from app.services.incident_note_service import (
    create_incident_note,
    get_incident_notes,
)
from app.services.incident_service import (
    assign_incident,
    create_incident,
    get_incident,
    get_incidents,
    update_status,
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
    Change an incident's status.

    The authenticated user performing the transition is recorded in the
    incident activity timeline.
    """
    incident = await update_status(
        db=db,
        incident_id=incident_id,
        status=status,
        actor_user_id=current_user.id,
    )

    if not incident:
        raise HTTPException(
            status_code=404,
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
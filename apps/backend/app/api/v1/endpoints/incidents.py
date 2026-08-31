from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_role
from app.db.session import get_db

from app.models.incident import IncidentStatus
from app.models.user import User, UserRole

from app.schemas.incident import (
    IncidentAssign,
    IncidentCreate,
    IncidentResponse,
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
    _: User = Depends(
        require_role(
            UserRole.ADMIN,
            UserRole.ANALYST,
        )
    ),
):
    return await create_incident(
        db=db,
        title=incident.title,
        description=incident.description,
        severity=incident.severity,
        event_id=incident.event_id,
    )


@router.get(
    "/",
    response_model=list[IncidentResponse],
)
async def list_incidents(
    db: AsyncSession = Depends(get_db),
):
    return await get_incidents(db)


@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
)
async def read_incident(
    incident_id: int,
    db: AsyncSession = Depends(get_db),
):
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
    _: User = Depends(
        require_role(
            UserRole.ADMIN,
            UserRole.ANALYST,
        )
    ),
):
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
    _: User = Depends(
        require_role(
            UserRole.ADMIN,
            UserRole.ANALYST,
        )
    ),
):
    incident = await update_status(
        db,
        incident_id,
        status,
    )

    if not incident:
        raise HTTPException(
            status_code=404,
            detail="Incident not found",
        )

    return incident
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

from app.schemas.incident import (
    IncidentCreate,
    IncidentResponse,
)

from app.models.incident import IncidentStatus

from app.services.incident_service import (
    create_incident,
    get_incidents,
    get_incident,
    assign_incident,
    update_status,
)


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
    "/{incident_id}/assign/{analyst}",
    response_model=IncidentResponse,
)
async def assign(
    incident_id: int,
    analyst: str,
    db: AsyncSession = Depends(get_db),
):
    incident = await assign_incident(
        db,
        incident_id,
        analyst,
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
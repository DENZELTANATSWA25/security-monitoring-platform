# HTTP endpoints for external telemetry ingestion.

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ingestion_auth import require_ingestion_api_key
from app.db.session import get_db
from app.schemas.ingestion import TelemetryEventCreate
from app.schemas.security_event import SecurityEventResponse
from app.services.ingestion_service import ingest_telemetry_event

router = APIRouter(
    prefix="/ingestion",
    tags=["Telemetry Ingestion"],
)

@router.post(
    "/events",
    response_model=SecurityEventResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[
        Depends(require_ingestion_api_key),
    ],
)
async def ingest_event(
    telemetry: TelemetryEventCreate,
    db: AsyncSession = Depends(get_db),
):
    # Receive a security event from an authenticated external producer.

    return await ingest_telemetry_event(
        db=db,
        telemetry=telemetry,
    )
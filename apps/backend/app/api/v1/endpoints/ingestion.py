"""HTTP endpoints for external telemetry ingestion."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.ingestion_rate_limit import require_ingestion_rate_limit
from app.db.session import get_db
from app.models.telemetry_source import TelemetrySource
from app.schemas.ingestion import TelemetryEventCreate
from app.schemas.security_event import SecurityEventResponse
from app.services.ingestion_service import ingest_telemetry_event
from app.services.telemetry_source_service import mark_telemetry_source_seen


router = APIRouter(
    prefix="/ingestion",
    tags=["Telemetry Ingestion"],
)


@router.post(
    "/events",
    response_model=SecurityEventResponse,
    status_code=status.HTTP_201_CREATED,
)
async def ingest_event(
    telemetry: TelemetryEventCreate,
    db: AsyncSession = Depends(get_db),
    telemetry_source: TelemetrySource = Depends(require_ingestion_rate_limit),
):
    """Receive a security event from an authenticated telemetry producer."""

    await mark_telemetry_source_seen(
        db=db,
        source=telemetry_source,
    )

    return await ingest_telemetry_event(
        db=db,
        telemetry=telemetry,
        telemetry_source=telemetry_source,
    )

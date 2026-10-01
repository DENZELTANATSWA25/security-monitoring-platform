# Application service for external telemetry ingestion.

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security_event import SecurityEvent
from app.schemas.ingestion import TelemetryEventCreate
from app.schemas.security_event import SecurityEventCreate
from app.services.event_service import create_event

async def ingest_telemetry_event(
        db: AsyncSession,
        telemetry: TelemetryEventCreate,
) -> SecurityEvent:
    # Normalise external telemetry and pass it into the canonical event processing pipeline.

    event_data = SecurityEventCreate(
        event_type=telemetry.event_type,
        severity=telemetry.severity,
        source=telemetry.source,
        description=telemetry.description,
        user_id=None,
        event_metadata=telemetry.event_metadata,
        occurred_at=telemetry.occurred_at,
    )

    return await create_event(
        db=db,
        event_data=event_data,
    )

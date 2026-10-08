from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from pathlib import Path

from app.core.websocket_manager import manager
from app.models.security_event import SecurityEvent
from app.schemas.security_event import SecurityEventCreate
from app.services.alert_service import create_alert
from app.services.detection.engine import run_detection
from app.services.detection.base import DetectionContext
from app.core.config import settings
from app.services.anomaly_detection.detector import detect_anomaly


async def create_event(
    db: AsyncSession,
    event_data: SecurityEventCreate,
) -> SecurityEvent:
    """
    Create a security event and run detection against it.

    Database changes produced by this workflow are committed together.
    The WebSocket notification is sent only after the database transaction
    has completed successfully.
    """


    event = SecurityEvent(
        event_type=event_data.event_type,
        severity=event_data.severity,
        source=event_data.source,
        message=event_data.description,
        user_id=event_data.user_id,
        telemetry_source_id=event_data.telemetry_source_id,
        event_metadata=event_data.event_metadata,
        occurred_at=event_data.occurred_at,
    )

    db.add(event)

    try:
        # Flush so the event receives its database-generated ID while
        # keeping the transaction open.
        await db.flush()

        context = DetectionContext(
            event=event,
        )

        results = await run_detection(
            db,
            context,
        )

        for result in results:
            await create_alert(
                db=db,
                alert_type=result.alert_type,
                severity=result.severity,
                message=result.message,
            )

        # Run ML anomaly detection independently from deterministic rules.
        anomaly_result = detect_anomaly(
            event,
            model_directory=Path(
                settings.ANOMALY_MODEL_DIRECTORY
            ),
        )

        if anomaly_result.available and anomaly_result.is_anomaly:
            await create_alert(
                db=db,
                alert_type="ML_ANOMALY",
                severity="WARNING",
                message=(
                    "ML anomaly detected for security event "
                    f"{event.id}. "
                    f"Model: {anomaly_result.model_version}. "
                    f"Score: {anomaly_result.score:.6f}. "
                    f"{anomaly_result.reason}"
                ),
            )

        # Event and generated alerts become permanent together.
        await db.commit()

    except Exception:
        # Restore the session to a usable state and ensure partial
        # ingestion is never persisted.
        await db.rollback()
        raise

    await db.refresh(event)

    # External side effects happen after the database commit because a
    # WebSocket message cannot participate in a database rollback.
    await manager.broadcast(
        {
            "type": "security_event",
            "event": {
                "id": event.id,
                "event_type": event.event_type,
                "severity": event.severity.value,
                "source": event.source,
                "message": event.message,
                "created_at": event.created_at.isoformat(),
            },
        }
    )

    return event
"""Application workflow for training the anomaly-detection model."""

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security_event import SecurityEvent
from app.services.anomaly_detection.model import AnomalyModelConfig
from app.services.anomaly_detection.model_store import save_anomaly_model
from app.services.anomaly_detection.trainer import (
    MINIMUM_TRAINING_EVENTS,
    train_anomaly_model,
)

async def train_from_historical_events(
    db: AsyncSession,
    *,
    model_directory: Path,
    version: str,
    config: AnomalyModelConfig | None = None,
    limit: int = 10_000,
) -> int:
    """
    Train and persist an anomaly model from historical security events.

    Returns the number of events used for training.
    """

    if limit < MINIMUM_TRAINING_EVENTS:
        raise ValueError(
            f"Training limit must be at least "
            f"{MINIMUM_TRAINING_EVENTS}."
        )

    result = await db.execute(
        select(SecurityEvent)
        .order_by(
            SecurityEvent.created_at.asc(),
            SecurityEvent.id.asc(),
        )
        .limit(limit)
    )

    events = list(
        result.scalars().all()
    )

    model = train_anomaly_model(
        events,
        config=config,   
    )

    save_anomaly_model(
        model,
        directory=model_directory,
        version=version,
    )

    return len(events)
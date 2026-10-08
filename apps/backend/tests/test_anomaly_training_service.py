"""Tests for the anomaly-model training workflow."""

from pathlib import Path

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security_event import EventSeverity, SecurityEvent
from app.services.anomaly_detection.model_store import load_anomaly_model
from app.services.anomaly_detection.trainer import MINIMUM_TRAINING_EVENTS
from app.services.anomaly_detection.training_service import (
    train_from_historical_events,
)


async def test_training_service_trains_and_persists_model(
    db_session: AsyncSession,
    tmp_path: Path,
) -> None:
    """Historical database events should produce a persisted model."""

    events = [
        SecurityEvent(
            event_type="TRAINING_EVENT",
            severity=EventSeverity.INFO,
            source="training-test",
            message=f"Normal training event {index}",
            telemetry_source_id=None,
            event_metadata={
                "environment": "test",
            },
        )
        for index in range(
            MINIMUM_TRAINING_EVENTS
        )
    ]

    db_session.add_all(events)
    await db_session.flush()

    event_count = await train_from_historical_events(
        db_session,
        model_directory=tmp_path,
        version="test-v1",
    )

    stored = load_anomaly_model(
        directory=tmp_path,
    )

    assert event_count == MINIMUM_TRAINING_EVENTS
    assert stored is not None
    assert stored.version == "test-v1"


async def test_training_service_rejects_insufficient_history(
    db_session: AsyncSession,
    tmp_path: Path,
) -> None:
    """Training should fail when historical data is insufficient."""

    events = [
        SecurityEvent(
            event_type="SMALL_TRAINING_SET",
            severity=EventSeverity.INFO,
            source="training-test",
            message=f"Training event {index}",
        )
        for index in range(
            MINIMUM_TRAINING_EVENTS - 1
        )
    ]

    db_session.add_all(events)
    await db_session.flush()

    with pytest.raises(
        ValueError,
        match="events are required",
    ):
        await train_from_historical_events(
            db_session,
            model_directory=tmp_path,
            version="test-v1",
        )


async def test_training_service_rejects_too_small_limit(
    db_session: AsyncSession,
    tmp_path: Path,
) -> None:
    """Training limits below the minimum dataset size are invalid."""

    with pytest.raises(
        ValueError,
        match="Training limit must be at least",
    ):
        await train_from_historical_events(
            db_session,
            model_directory=tmp_path,
            version="test-v1",
            limit=MINIMUM_TRAINING_EVENTS - 1,
        )
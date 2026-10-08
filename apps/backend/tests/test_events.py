"""Regression tests for security event creation."""

from sqlalchemy.ext.asyncio import AsyncSession
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security_event import EventSeverity, SecurityEvent
from app.schemas.security_event import SecurityEventCreate
from app.services.event_service import create_event
from app.models.alert import Alert
from app.services.detection.result import DetectionResult
from app.services.anomaly_detection.result import AnomalyResult


async def test_event_can_be_created_without_metadata(
    db_session: AsyncSession,
) -> None:
    """Optional event metadata must genuinely be optional."""

    event_data = SecurityEventCreate(
        event_type="TEST_EVENT_WITHOUT_METADATA",
        severity=EventSeverity.INFO,
        source="pytest",
        description="Event intentionally created without metadata.",
        event_metadata=None,
    )

    event = await create_event(
        db=db_session,
        event_data=event_data,
    )

    assert event.id is not None
    assert event.event_type == "TEST_EVENT_WITHOUT_METADATA"
    assert event.event_metadata is None


async def test_event_can_be_created_with_metadata(
    db_session: AsyncSession,
) -> None:
    """Metadata supplied with an event should be persisted."""

    event_data = SecurityEventCreate(
        event_type="TEST_EVENT_WITH_METADATA",
        severity=EventSeverity.WARNING,
        source="pytest",
        description="Event containing metadata.",
        event_metadata={
            "email": "security@example.com",
            "ip": "203.0.113.10",
        },
    )

    event = await create_event(
        db=db_session,
        event_data=event_data,
    )

    assert event.id is not None
    assert event.event_metadata == {
        "email": "security@example.com",
        "ip": "203.0.113.10",
    }

async def test_event_is_rolled_back_when_detection_fails(
    db_session: AsyncSession,
) -> None:
    """
    Event creation must be atomic with detection processing.

    If detection fails after the event has bee flushed, the event must not remain persisted in the database.
    """
    event_type = "ATOMIC_ROLLBACK_TEST"

    event_data = SecurityEventCreate(
        event_type=event_type,
        severity=EventSeverity.INFO,
        source="pytest",
        description="Event used to verify transaction rollback.",
        event_metadata={
            "email": "rollback@example.com",
        },
    )


    with patch(
        "app.services.event_service.run_detection",
        new=AsyncMock(
            side_effect=RuntimeError(
                "Simulated detection failure."
            )
        ),
    ):
        with pytest.raises(
            RuntimeError,
            match="Simulated detection failure.",
        ):
            await create_event(
                db=db_session,
                event_data=event_data,
            )

    # The same session must remain usable after create_event() performs its rollback
    result = await db_session.execute(
        select(SecurityEvent).where(
            SecurityEvent.event_type == event_type,
        )
    )

    persisted_event = result.scalar_one_or_none()

    assert persisted_event is None

async def test_event_is_rolled_back_when_alert_creation_fails(
    db_session: AsyncSession,
) -> None:
    """
    Event creation and generated alerts must be atomic.

    If alert creation fails after detection succeeds, the security event
    must not remain persisted in the database.
    """
    event_type = "ALERT_ROLLBACK_TEST"

    event_data = SecurityEventCreate(
        event_type=event_type,
        severity=EventSeverity.CRITICAL,
        source="pytest",
        description="Event used to verify alert transaction rollback.",
        event_metadata={
            "email": "alert-rollback@example.com",
        },
    )

    detection_result = [
        DetectionResult.triggered_alert(
            alert_type="TEST_ALERT",
            severity="CRITICAL",
            message="Simulated detection alert.",
        )
    ]

    with patch(
        "app.services.event_service.run_detection",
        new=AsyncMock(
            return_value=detection_result,
        ),
    ):
        with patch(
            "app.services.event_service.create_alert",
            new=AsyncMock(
                side_effect=RuntimeError(
                    "Simulated alert creation failure"
                )
            ),
        ):
            with pytest.raises(
                RuntimeError,
                match="Simulated alert creation failure",
            ):
                await create_event(
                    db=db_session,
                    event_data=event_data,
                )

    result = await db_session.execute(
        select(SecurityEvent).where(
            SecurityEvent.event_type == event_type,
        )
    )

    persisted_event = result.scalar_one_or_none()

    assert persisted_event is None

async def test_event_and_flushed_alert_are_rolled_back_when_later_alert_fails(
    db_session: AsyncSession,
) -> None:
    """
    Event ingestion must roll back all database changes when a later
    alert fails.

    This verifies that an event and an alert that have both already been
    flushed are removed when the overall workflow fails.
    """
    event_type = "MULTI_ALERT_ROLLBACK_TEST"
    alert_type = "FIRST_ATOMIC_TEST_ALERT"

    event_data = SecurityEventCreate(
        event_type=event_type,
        severity=EventSeverity.CRITICAL,
        source="pytest",
        description="Event used to verify multi-alert rollback.",
        event_metadata={
            "email": "multi-alert-rollback@example.com",
        },
    )

    detection_results = [
        DetectionResult.triggered_alert(
            alert_type=alert_type,
            severity="CRITICAL",
            message="First alert should eventually be rolled back.",
        ),
        DetectionResult.triggered_alert(
            alert_type="SECOND_ATOMIC_TEST_ALERT",
            severity="CRITICAL",
            message="Second alert triggers simulated failure.",
        ),
    ]

    # Import the real implementation before patching the symbol used by
    # event_service.
    from app.services.alert_service import create_alert as real_create_alert

    call_count = 0

    async def create_alert_then_fail(**kwargs):
        """
        Persist the first alert normally, then simulate a failure while
        processing the second alert.
        """
        nonlocal call_count
        call_count += 1

        if call_count == 1:
            return await real_create_alert(**kwargs)

        raise RuntimeError(
            "Simulated second alert creation failure"
        )

    with patch(
        "app.services.event_service.run_detection",
        new=AsyncMock(
            return_value=detection_results,
        ),
    ):
        with patch(
            "app.services.event_service.create_alert",
            side_effect=create_alert_then_fail,
        ):
            with pytest.raises(
                RuntimeError,
                match="Simulated second alert creation failure",
            ):
                await create_event(
                    db=db_session,
                    event_data=event_data,
                )

    assert call_count == 2

    event_result = await db_session.execute(
        select(SecurityEvent).where(
            SecurityEvent.event_type == event_type,
        )
    )

    persisted_event = event_result.scalar_one_or_none()

    alert_result = await db_session.execute(
        select(Alert).where(
            Alert.alert_type == alert_type,
        )
    )

    persisted_alert = alert_result.scalar_one_or_none()

    assert persisted_event is None
    assert persisted_alert is None

async def test_fifth_event_from_same_source_creates_event_burst_alert(
    db_session: AsyncSession,
) -> None:
    """
    Five recent security events from the same source should generate an
    EVENT_BURST alert through the complete event-ingestion workflow.
    """

    source = "burst-integration-source"

    for index in range(5):
        event_data = SecurityEventCreate(
            event_type=f"BURST_INTEGRATION_EVENT_{index}",
            severity=EventSeverity.WARNING,
            source=source,
            description=f"Burst integration event {index}",
            event_metadata={
                "ip": "203.0.113.50",
            },
        )

        await create_event(
            db=db_session,
            event_data=event_data,
        )

    result = await db_session.execute(
        select(Alert).where(
            Alert.alert_type == "EVENT_BURST",
        )
    )

    alerts = result.scalars().all()

    assert len(alerts) == 1

    alert = alerts[0]

    assert alert.severity == "HIGH"
    assert alert.message is not None
    assert source in alert.message

async def test_event_occurrence_time_is_persisted(
    db_session: AsyncSession,
) -> None:
    """Source occurrence time should be preserved separately from ingestion time."""

    from datetime import datetime

    occurred_at = datetime(
        2026,
        10,
        1,
        18,
        30,
        0,
    )

    event_data = SecurityEventCreate(
        event_type="EXTERNAL_TIMESTAMP_TEST",
        severity=EventSeverity.WARNING,
        source="linux-server-01",
        description="External telemetry event.",
        occurred_at=occurred_at,
    )

    event = await create_event(
        db=db_session,
        event_data=event_data,
    )

    assert event.occurred_at == occurred_at
    assert event.created_at is not None

async def test_identical_events_are_stored_as_distinct_occurrences(
    db_session: AsyncSession,
) -> None:
    """Repeated telemetry must not be discarded based on message equality."""

    event_data = SecurityEventCreate(
        event_type="SSH_LOGIN_FAILURE",
        severity=EventSeverity.WARNING,
        source="linux-server-01",
        description="Failed password for root",
    )

    first_event = await create_event(
        db=db_session,
        event_data=event_data,
    )

    second_event = await create_event(
        db=db_session,
        event_data=event_data,
    )

    assert first_event.id != second_event.id

    result = await db_session.execute(
        select(SecurityEvent).where(
            SecurityEvent.event_type == "SSH_LOGIN_FAILURE",
            SecurityEvent.source == "linux-server-01",
        )
    )

    events = result.scalars().all()

    assert len(events) == 2

async def test_event_creation_continues_when_anomaly_detection_is_unavailable(
    db_session: AsyncSession,
) -> None:
    """Unavailable ML detection must not prevent event ingestion."""

    event_type = "ML_UNAVAILABLE_INTEGRATION_TEST"

    event_data = SecurityEventCreate(
        event_type=event_type,
        severity=EventSeverity.INFO,
        source="pytest-ml",
        description="Event created while ML detection is unavailable.",
    )

    with patch(
        "app.services.event_service.detect_anomaly",
        return_value=AnomalyResult.unavailable(
            reason="No trained anomaly model is available.",
        ),
    ):
        event = await create_event(
            db=db_session,
            event_data=event_data,
        )

    assert event.id is not None

    result = await db_session.execute(
        select(SecurityEvent).where(
            SecurityEvent.id == event.id,
        )
    )

    persisted_event = result.scalar_one_or_none()

    assert persisted_event is not None
    assert persisted_event.event_type == event_type

    alert_result = await db_session.execute(
        select(Alert).where(
            Alert.alert_type == "ML_ANOMALY",
        )
    )

    ml_alert = alert_result.scalar_one_or_none()

    assert ml_alert is None


async def test_normal_ml_result_does_not_create_anomaly_alert(
    db_session: AsyncSession,
) -> None:
    """A normal ML classification must not generate an anomaly alert."""

    event_data = SecurityEventCreate(
        event_type="ML_NORMAL_INTEGRATION_TEST",
        severity=EventSeverity.INFO,
        source="pytest-ml",
        description="Event classified as normal by ML.",
    )

    with patch(
        "app.services.event_service.detect_anomaly",
        return_value=AnomalyResult.normal(
            score=0.123456,
            model_version="v1",
        ),
    ):
        event = await create_event(
            db=db_session,
            event_data=event_data,
        )

    assert event.id is not None

    result = await db_session.execute(
        select(Alert).where(
            Alert.alert_type == "ML_ANOMALY",
        )
    )

    ml_alert = result.scalar_one_or_none()

    assert ml_alert is None


async def test_anomalous_ml_result_creates_anomaly_alert(
    db_session: AsyncSession,
) -> None:
    """An anomalous ML classification should generate an ML alert."""

    event_data = SecurityEventCreate(
        event_type="ML_ANOMALY_INTEGRATION_TEST",
        severity=EventSeverity.WARNING,
        source="pytest-ml",
        description="Event classified as anomalous by ML.",
    )

    with patch(
        "app.services.event_service.detect_anomaly",
        return_value=AnomalyResult.anomalous(
            score=-0.314159,
            model_version="v1",
            reason=(
                "Event behaviour differs from the model's "
                "learned baseline."
            ),
        ),
    ):
        event = await create_event(
            db=db_session,
            event_data=event_data,
        )

    assert event.id is not None

    result = await db_session.execute(
        select(Alert).where(
            Alert.alert_type == "ML_ANOMALY",
        )
    )

    ml_alert = result.scalar_one_or_none()

    assert ml_alert is not None
    assert ml_alert.severity == "WARNING"
    assert f"security event {event.id}" in ml_alert.message
    assert "Model: v1" in ml_alert.message
    assert "Score: -0.314159" in ml_alert.message
    assert (
        "Event behaviour differs from the model's learned baseline."
        in ml_alert.message
    )
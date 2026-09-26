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
        {
            "triggered": True,
            "alert_type": "TEST_ALERT",
            "severity": "CRITICAL",
            "message": "Simulated detection alert.",
        }
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
        {
            "triggered": True,
            "alert_type": alert_type,
            "severity": "CRITICAL",
            "message": "First alert should eventually be rolled back.",
        },
        {
            "triggered": True,
            "alert_type": "SECOND_ATOMIC_TEST_ALERT",
            "severity": "CRITICAL",
            "message": "Second alert triggers simulated failure.",
        },
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
"""Phase 6C: event-processing reliability and failure recovery."""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import func, select

from app.models.security_event import SecurityEvent
from app.schemas.security_event import SecurityEventCreate
from app.services.event_service import create_event


pytestmark = pytest.mark.asyncio


def make_event_data(event_type: str) -> SecurityEventCreate:
    """Construct a synthetic event for failure-injection testing."""
    return SecurityEventCreate(
        event_type=event_type,
        severity="WARNING",
        source="phase-6c-reliability-evaluation",
        description="Synthetic reliability evaluation event",
        user_id=None,
    )


async def count_events(db_session, event_type: str) -> int:
    """Count events created by an individual evaluation scenario."""
    result = await db_session.execute(
        select(func.count(SecurityEvent.id)).where(
            SecurityEvent.event_type == event_type
        )
    )
    return result.scalar_one()


async def test_detection_failure_rolls_back_event(
    db_session,
):
    event_type = "PHASE_6C_DETECTION_FAILURE"

    with (
        patch(
            "app.services.event_service.run_detection",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Synthetic detection failure"),
        ),
        patch(
            "app.services.event_service.manager.broadcast",
            new_callable=AsyncMock,
        ) as broadcast,
    ):
        with pytest.raises(
            RuntimeError,
            match="Synthetic detection failure",
        ):
            await create_event(
                db=db_session,
                event_data=make_event_data(event_type),
            )

        broadcast.assert_not_awaited()

    assert await count_events(db_session, event_type) == 0


async def test_alert_failure_rolls_back_event(
    db_session,
):
    event_type = "PHASE_6C_ALERT_FAILURE"

    # A synthetic detection result forces the alert-creation path.
    detection_result = type(
        "SyntheticDetectionResult",
        (),
        {
            "alert_type": "PHASE_6C_TEST_ALERT",
            "severity": "HIGH",
            "message": "Synthetic detection result",
        },
    )()

    with (
        patch(
            "app.services.event_service.run_detection",
            new_callable=AsyncMock,
            return_value=[detection_result],
        ),
        patch(
            "app.services.event_service.create_alert",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Synthetic alert failure"),
        ),
        patch(
            "app.services.event_service.manager.broadcast",
            new_callable=AsyncMock,
        ) as broadcast,
    ):
        with pytest.raises(
            RuntimeError,
            match="Synthetic alert failure",
        ):
            await create_event(
                db=db_session,
                event_data=make_event_data(event_type),
            )

        broadcast.assert_not_awaited()

    assert await count_events(db_session, event_type) == 0


async def test_websocket_failure_occurs_after_commit(
    db_session,
):
    event_type = "PHASE_6C_WEBSOCKET_FAILURE"

    with (
        patch(
            "app.services.event_service.run_detection",
            new_callable=AsyncMock,
            return_value=[],
        ),
        patch(
            "app.services.event_service.detect_anomaly",
        ) as anomaly,
        patch(
            "app.services.event_service.manager.broadcast",
            new_callable=AsyncMock,
            side_effect=RuntimeError("Synthetic WebSocket failure"),
        ),
    ):
        # Prevent the optional ML detector from affecting this test.
        anomaly.return_value.available = False

        with pytest.raises(
            RuntimeError,
            match="Synthetic WebSocket failure",
        ):
            await create_event(
                db=db_session,
                event_data=make_event_data(event_type),
            )

    # The transaction commits before the broadcast is attempted.
    assert await count_events(db_session, event_type) == 1

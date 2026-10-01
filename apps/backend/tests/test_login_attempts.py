"""Tests for authentication-attempt recording and detection transactions."""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.login_attempt import LoginAttempt
from app.services.login_attempt_service import (
    count_failed_attempts,
    record_login_attempt,
)
from app.services.detection.result import DetectionResult


async def test_successful_login_attempt_is_recorded(
    db_session: AsyncSession,
) -> None:
    """A successful authentication attempt should be persisted."""

    attempt = await record_login_attempt(
        db=db_session,
        email="successful@example.com",
        successful=True,
        ip_address="192.0.2.10",
    )

    assert attempt.id is not None
    assert attempt.email == "successful@example.com"
    assert attempt.successful is True
    assert attempt.ip_address == "192.0.2.10"
    assert attempt.timestamp is not None

    result = await db_session.execute(
        select(LoginAttempt).where(
            LoginAttempt.id == attempt.id,
        )
    )
    stored_attempt = result.scalar_one_or_none()

    assert stored_attempt is not None
    assert stored_attempt.email == "successful@example.com"


async def test_failed_login_attempt_is_recorded(
    db_session: AsyncSession,
) -> None:
    """A failed authentication attempt should be persisted."""

    attempt = await record_login_attempt(
        db=db_session,
        email="failed@example.com",
        successful=False,
        ip_address="192.0.2.20",
    )

    assert attempt.id is not None
    assert attempt.email == "failed@example.com"
    assert attempt.successful is False
    assert attempt.ip_address == "192.0.2.20"

    failed_count = await count_failed_attempts(
        db=db_session,
        email="failed@example.com",
    )

    assert failed_count == 1


async def test_missing_ip_address_uses_default(
    db_session: AsyncSession,
) -> None:
    """Login attempts without an IP address should use the safe default."""

    attempt = await record_login_attempt(
        db=db_session,
        email="no-ip@example.com",
        successful=True,
        ip_address=None,
    )

    assert attempt.ip_address == "0.0.0.0"


async def test_fifth_failed_attempt_creates_brute_force_alert(
    db_session: AsyncSession,
) -> None:
    """Five recent failures for one account should trigger brute-force detection."""

    email = "bruteforce@example.com"

    for index in range(5):
        await record_login_attempt(
            db=db_session,
            email=email,
            successful=False,
            ip_address=f"192.0.2.{index + 1}",
        )

    failed_count = await count_failed_attempts(
        db=db_session,
        email=email,
    )

    assert failed_count == 5

    result = await db_session.execute(
        select(Alert).where(
            Alert.alert_type == "BRUTE_FORCE_ATTACK",
            Alert.message == f"Brute force attack detected on {email}",
            Alert.resolved.is_(False),
        )
    )
    alert = result.scalar_one_or_none()

    assert alert is not None
    assert alert.severity == "CRITICAL"


async def test_login_attempt_is_rolled_back_when_detection_fails(
    db_session: AsyncSession,
) -> None:
    """
    A detection failure must roll back the authentication attempt.

    This verifies that recording the attempt and running detection belong to
    the same transaction.
    """

    email = "detection-rollback@example.com"

    with patch(
        "app.services.detection.engine.run_detection",
        new=AsyncMock(
            side_effect=RuntimeError("Detection engine failure"),
        ),
    ):
        with pytest.raises(
            RuntimeError,
            match="Detection engine failure",
        ):
            await record_login_attempt(
                db=db_session,
                email=email,
                successful=False,
                ip_address="192.0.2.30",
            )

    result = await db_session.execute(
        select(func.count(LoginAttempt.id)).where(
            LoginAttempt.email == email,
        )
    )

    assert result.scalar_one() == 0


async def test_login_attempt_is_rolled_back_when_alert_creation_fails(
    db_session: AsyncSession,
) -> None:
    """
    Alert creation failure must roll back the authentication attempt.

    Detection is mocked as triggered so execution reaches create_alert().
    """

    email = "alert-rollback@example.com"

    detection_result = [
        DetectionResult.triggered_alert(
            alert_type="TEST_DETECTION",
            severity="CRITICAL",
            message="Synthetic detection for rollback testing",
        )
    ]

    with (
        patch(
            "app.services.detection.engine.run_detection",
            new=AsyncMock(
                return_value=detection_result,
            ),
        ),
        patch(
            "app.services.alert_service.create_alert",
            new=AsyncMock(
                side_effect=RuntimeError("Alert creation failure"),
            ),
        ),
    ):
        with pytest.raises(
            RuntimeError,
            match="Alert creation failure",
        ):
            await record_login_attempt(
                db=db_session,
                email=email,
                successful=False,
                ip_address="192.0.2.40",
            )

    attempt_result = await db_session.execute(
        select(func.count(LoginAttempt.id)).where(
            LoginAttempt.email == email,
        )
    )

    assert attempt_result.scalar_one() == 0


async def test_successful_attempt_does_not_run_detection(
    db_session: AsyncSession,
) -> None:
    """Successful authentication should not invoke threat detection."""

    with patch(
        "app.services.detection.engine.run_detection",
        new=AsyncMock(),
    ) as mocked_detection:
        await record_login_attempt(
            db=db_session,
            email="successful-no-detection@example.com",
            successful=True,
            ip_address="192.0.2.50",
        )

    mocked_detection.assert_not_awaited()

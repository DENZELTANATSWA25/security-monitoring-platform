"""Tests for authentication-attempt recording and detection transactions."""

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from datetime import datetime, timedelta
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

async def test_login_attempt_location_is_persisted(
    db_session: AsyncSession,
) -> None:
    """Login-attempt coordinates should be persisted when supplied."""

    attempt = await record_login_attempt(
        db=db_session,
        email="location@example.com",
        successful=True,
        ip_address="203.0.113.10",
        latitude=51.5074,
        longitude=-0.1278,
    )

    assert attempt.latitude == pytest.approx(51.5074)
    assert attempt.longitude == pytest.approx(-0.1278)

    result = await db_session.execute(
        select(LoginAttempt).where(
            LoginAttempt.id == attempt.id,
        )
    )

    stored_attempt = result.scalar_one()

    assert stored_attempt.latitude == pytest.approx(51.5074)
    assert stored_attempt.longitude == pytest.approx(-0.1278)


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


async def test_successful_attempt_runs_detection(
    db_session: AsyncSession,
) -> None:
    """Successful authentication should be evaluated by detection rules."""

    with patch(
        "app.services.detection.engine.run_detection",
        new=AsyncMock(return_value=[]),
    ) as mocked_detection:
        attempt = await record_login_attempt(
            db=db_session,
            email="successful-detection@example.com",
            successful=True,
            ip_address="192.0.2.50",
        )

    mocked_detection.assert_awaited_once()

    _, context = mocked_detection.await_args.args

    assert context.login_attempt is attempt


async def test_first_successful_login_does_not_create_suspicious_login_alert(
    db_session: AsyncSession,
) -> None:
    """An account's first successful login should establish its baseline."""

    email = "first-login@example.com"

    await record_login_attempt(
        db=db_session,
        email=email,
        successful=True,
        ip_address="192.0.2.100",
    )

    result = await db_session.execute(
        select(Alert).where(
            Alert.alert_type == "SUSPICIOUS_LOGIN",
            Alert.message.contains(email),
        )
    )

    assert result.scalar_one_or_none() is None


async def test_known_successful_login_ip_does_not_create_alert(
    db_session: AsyncSession,
) -> None:
    """Repeated successful logins from a known IP should not be suspicious."""

    email = "known-ip@example.com"
    ip_address = "192.0.2.110"

    await record_login_attempt(
        db=db_session,
        email=email,
        successful=True,
        ip_address=ip_address,
    )

    await record_login_attempt(
        db=db_session,
        email=email,
        successful=True,
        ip_address=ip_address,
    )

    result = await db_session.execute(
        select(Alert).where(
            Alert.alert_type == "SUSPICIOUS_LOGIN",
            Alert.message.contains(email),
        )
    )

    assert result.scalar_one_or_none() is None


async def test_new_successful_login_ip_creates_suspicious_login_alert(
    db_session: AsyncSession,
) -> None:
    """A new IP after established successful-login history should alert."""

    email = "new-ip@example.com"

    await record_login_attempt(
        db=db_session,
        email=email,
        successful=True,
        ip_address="192.0.2.120",
    )

    await record_login_attempt(
        db=db_session,
        email=email,
        successful=True,
        ip_address="203.0.113.120",
    )

    result = await db_session.execute(
        select(Alert).where(
            Alert.alert_type == "SUSPICIOUS_LOGIN",
            Alert.message.contains(email),
        )
    )

    alert = result.scalar_one_or_none()

    assert alert is not None
    assert alert.severity == "MEDIUM"
    assert "203.0.113.120" in alert.message


async def test_successful_ip_history_is_isolated_by_account(
    db_session: AsyncSession,
) -> None:
    """Another account's IP history must not establish trust for this account."""

    shared_ip = "192.0.2.130"

    await record_login_attempt(
        db=db_session,
        email="other-account@example.com",
        successful=True,
        ip_address=shared_ip,
    )

    await record_login_attempt(
        db=db_session,
        email="target-account@example.com",
        successful=True,
        ip_address="192.0.2.131",
    )

    await record_login_attempt(
        db=db_session,
        email="target-account@example.com",
        successful=True,
        ip_address=shared_ip,
    )

    result = await db_session.execute(
        select(Alert).where(
            Alert.alert_type == "SUSPICIOUS_LOGIN",
            Alert.message.contains("target-account@example.com"),
        )
    )

    alert = result.scalar_one_or_none()

    assert alert is not None
    assert shared_ip in alert.message

async def test_impossible_travel_creates_alert(
    db_session: AsyncSession,
) -> None:
    """
    Geographically impossible successful logins should create an alert
    through the real login-attempt detection workflow.
    """

    email = "impossible-travel@example.com"

    first_attempt = await record_login_attempt(
        db=db_session,
        email=email,
        successful=True,
        ip_address="192.0.2.220",
        latitude=51.5074,
        longitude=-0.1278,
    )

    # Move the first login into the past so the second login represents
    # London -> New York within thirty minutes.
    first_attempt.timestamp = datetime.utcnow() - timedelta(
        minutes=30,
    )

    await db_session.commit()

    await record_login_attempt(
        db=db_session,
        email=email,
        successful=True,
        ip_address="203.0.113.220",
        latitude=40.7128,
        longitude=-74.0060,
    )

    result = await db_session.execute(
        select(Alert).where(
            Alert.alert_type == "IMPOSSIBLE_TRAVEL",
        )
    )

    alerts = result.scalars().all()

    assert len(alerts) == 1
    assert alerts[0].severity == "HIGH"
    assert email in alerts[0].message
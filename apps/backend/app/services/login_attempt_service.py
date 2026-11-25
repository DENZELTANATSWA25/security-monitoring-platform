"""Persistence and detection for authentication attempts."""

import logging
from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.login_attempt import LoginAttempt
from app.services.behavioural_detection.login_adapter import (
    BehaviouralFeatureError,
    extract_login_behaviour,
)
from app.services.behavioural_detection.async_inference import (
    run_behavioural_inference,
)
from app.services.detection.base import DetectionContext


logger = logging.getLogger(__name__)

async def record_login_attempt(
    db: AsyncSession,
    email: str,
    successful: bool,
    ip_address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
) -> LoginAttempt:
    """
    Record an authentication attempt and run detection when it fails.

    The login attempt and any alerts generated from it are committed as
    one database transaction. If detection or alert creation fails, all
    changes made by this workflow are rolled back.
    """
    attempt = LoginAttempt(
        email=email,
        successful=successful,
        ip_address=ip_address or "0.0.0.0",
        latitude=latitude,
        longitude=longitude,
    )

    db.add(attempt)

    try:
        # Make the attempt visible to queries executed by the detection
        # engine without committing the transaction.
        await db.flush()

        # Every authentication attempt is evaluated by the detection engine.
        # Individual rules decide whether the attempt applies to them.
        from app.services.alert_service import create_alert
        from app.services.detection.engine import run_detection
    
        detection = await run_detection(
            db,
            DetectionContext(
                login_attempt=attempt,
            ),
        )

        for detection in detection:
            await create_alert(
                db=db,
                alert_type=detection.alert_type,
                severity=detection.severity,
                message=detection.message,
            )

        # Optional RF v3 shadow inference; never generates alerts.
        if settings.BEHAVIOURAL_RF_SHADOW_ENABLED:
            try:
                features = await extract_login_behaviour(
                    db,
                    attempt,
                )

            except BehaviouralFeatureError:
                # Invalid ML input must not interrupt authentication.
                logger.warning(
                    "Behavioural RF shadow features unavailable: "
                    "attempt_id=%s",
                    attempt.id,
                )

            else:
                result = await run_behavioural_inference(
                    features,
                    strategy="direct",
                )

                if result.available:
                    logger.info(
                        "Behavioural RF shadow prediction: "
                        "attempt_id=%s anomaly=%s score=%.6f model=%s",
                        attempt.id,
                        result.is_anomaly,
                        result.score,
                        result.model_version,
                    )
                else:
                    logger.warning(
                        "Behavioural RF shadow prediction unavailable: "
                        "attempt_id=%s reason=%s",
                        attempt.id,
                        result.reason,
                    )

        await db.commit()

    except Exception:
        await db.rollback()
        raise

    await db.refresh(attempt)

    return attempt

async def count_failed_attempts(
        db: AsyncSession,
        email: str
):
    five_minutes_ago = (
        datetime.utcnow()
        -
        timedelta(minutes=5)
    )
    
    result = await db.execute(
        select(func.count(LoginAttempt.id))
        .where(
            LoginAttempt.email == email,
            LoginAttempt.successful == False,
            LoginAttempt.timestamp > five_minutes_ago 
        )
    )

    return result.scalar()
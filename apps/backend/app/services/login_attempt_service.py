from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from sqlalchemy import select, func

from app.models.login_attempt import LoginAttempt
from app.services.detection.base import DetectionContext

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
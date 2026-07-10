from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from sqlalchemy import select, func

from app.models.login_attempt import LoginAttempt

async def record_login_attempt (
        db:AsyncSession,
        email: str,
        successful: bool,
        ip_address: str | None = None
):
    
    attempt = LoginAttempt(
        email=email,
        successful=successful,
        ip_address=ip_address or "0.0.0.0"
    )

    db.add(attempt)

    await db.commit()

    if not successful:
        from app.services.detection.engine import run_detection
        from app.services.alert_service import create_alert
        
        detections = await run_detection(
            db,
            {
                "email": email
            }
        )
        
        for detection in detections:
            await create_alert(
                db,
                detection["alert_type"],
                detection["severity"],
                detection["message"]
            )

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
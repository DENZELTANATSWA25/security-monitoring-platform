from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.alert import Alert
from app.models.security_event import SecurityEvent

from app.services.alert_service import create_alert
from app.services.security_detection_service import count_failed_attempts


async def detect_bruteforce(
        db: AsyncSession,
        email: str
):

    failed_count = await count_failed_attempts(
        db,
        email
    )

    if failed_count >= 5:

        message = (
            f"Brute force attack detected on {email}"
        )

        # Check existing unresolved alert
        result = await db.execute(
            select(Alert)
            .where(
                Alert.alert_type == "BRUTE_FORCE_ATTACK",
                Alert.message == message,
                Alert.resolved == False
            )
        )

        existing_alert = result.scalar_one_or_none()


        # Do not create duplicate alerts
        if existing_alert:
            return False


        # Create security event
        event = SecurityEvent(
            event_type="BRUTE_FORCE_ATTACK",
            severity="CRITICAL",
            source="auth-service",
            message=message,
        )

        db.add(event)

        await db.commit()


        # Create alert
        await create_alert(
            db,
            alert_type="BRUTE_FORCE_ATTACK",
            severity="CRITICAL",
            message=message
        )

        return True


    return False
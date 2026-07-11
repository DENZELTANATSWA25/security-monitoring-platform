from datetime import datetime, timedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.security_event import SecurityEvent, EventSeverity
from app.models.alert import Alert
from app.models.login_attempt import LoginAttempt

async def get_dashboard_summary(
        db: AsyncSession
):
    last_24_hours = (
        datetime.utcnow()
        -
        timedelta(hours=24)
    )

    total_events = await db.scalar(
        select(func.count(SecurityEvent.id))
    )

    critical_events = await db.scalar(
        select(func.count(SecurityEvent.id))
        .where(
            SecurityEvent.severity == EventSeverity.CRITICAL,
        )
    )

    active_alerts = await db.scalar(
        select(func.count(Alert.id))
        .where(
            Alert.resolved.is_(False)
        )
    )

    resolved_alerts = await db.scalar(
        select(func.count(Alert.id))
        .where(
            Alert.resolved.is_(True)
        )
    )

    failed_logins = await db.scalar(
        select(func.count(LoginAttempt.id))
        .where(
            LoginAttempt.successful.is_(True),
            LoginAttempt.timestamp > last_24_hours
        )
    )

    successful_logins = await db.scalar(
        select(func.count(LoginAttempt.id))
        .where(
            LoginAttempt.successful.is_(False),
            LoginAttempt.timestamp > last_24_hours
        )
    )

    return {
        "total_events": total_events or 0,
        "critical_events": critical_events or 0,
        "active_alerts": active_alerts or 0,
        "resolved_alerts": resolved_alerts or 0,
        "failed_logins_24h": failed_logins or 0,
        "successful_logins_24h": successful_logins or 0
    }
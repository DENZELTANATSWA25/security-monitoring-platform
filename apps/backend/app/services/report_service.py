from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert
from app.models.login_attempt import LoginAttempt
from app.models.security_event import (
    EventSeverity,
    SecurityEvent,
)

async def get_security_report(
        db: AsyncSession,
):
    last_24_hours = (
        datetime.utcnow()
        -
        timedelta(hours=24)
    )

    #---------------------------------------------
    # Main statistics
    #---------------------------------------------
    total_events = await db.scalar(
        select(func.count(SecurityEvent.id))
    )

    critical_events = await db.scalar(
        select(
            func.count(SecurityEvent.id)
        )
        .where(
            SecurityEvent.severity == EventSeverity.CRITICAL
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
            LoginAttempt.successful.is_(False),
            LoginAttempt.timestamp > last_24_hours
        )
    )

    successful_logins = await db.scalar(
        select(func.count(LoginAttempt.id))
        .where(
            LoginAttempt.successful.is_(True),
            LoginAttempt.timestamp > last_24_hours
        )
    )

    #---------------------------------------------
    # Event severity distribution
    #---------------------------------------------

    severity_result = await db.execute(
        select(
            SecurityEvent.severity,
            func.count(SecurityEvent.id)
        )
        .group_by(SecurityEvent.severity)
    )

    severity_rows = severity_result.all()

    severity_distribution = []

    for severity, count in severity_rows:
        severity_distribution.append(
            {
                "name": (
                    severity.value
                    if hasattr(severity, "value")
                    else str(severity)
                ),
                "count": count,
            }
        )

    #---------------------------------------------
    # Event type distribution
    #---------------------------------------------

    event_type_result = await db.execute(
        select(
            SecurityEvent.event_type,
            func.count(SecurityEvent.id)
        )
        .group_by(
            SecurityEvent.event_type
        )
        .order_by(
            func.count(SecurityEvent.id).desc()
        )
    )

    event_type_rows = (
        event_type_result.all()
    )

    event_type_distribution = []

    for event_type, count in event_type_rows:
        event_type_distribution.append(
            {
                "name": event_type,
                "count": count,
            }
        )

    #---------------------------------------------
    # Alert severity distribution
    #---------------------------------------------

    alert_severity_result = await db.execute(
        select(
            Alert.severity,
            func.count(Alert.id)
        )
        .group_by(Alert.severity)
    )

    alert_severity_rows = (
        alert_severity_result.all()
    )

    alert_severity_distribution = []

    for severity, count in alert_severity_rows:
        alert_severity_distribution.append(
            {
                "name": severity,
                "count": count,
            }
        )

    return {
        "total_events": (
            total_events or 0
        ),
        "critical_events": (
            critical_events or 0
        ),
        "active_alerts": (
            active_alerts or 0
        ),
        "resolved_alerts": (
            resolved_alerts or 0
        ),
        "failed_logins_24h": (
            failed_logins or 0
        ),
        "successful_logins_24h": (
            successful_logins or 0
        ),
        "severity_distribution":
            severity_distribution,
        "event_type_distribution":
            event_type_distribution,
        "alert_severity_distribution":
            alert_severity_distribution
    }

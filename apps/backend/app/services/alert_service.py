from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert


async def create_alert(
    db: AsyncSession,
    alert_type: str,
    severity: str,
    message: str
):

    alert = Alert(
        alert_type=alert_type,
        severity=severity,
        message=message
    )

    db.add(alert)

    await db.commit()

    await db.refresh(alert)

    return alert
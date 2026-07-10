from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.alert import Alert


async def create_alert(
    db: AsyncSession,
    alert_type: str,
    severity: str,
    message: str
):

    # prevent duplicate active alerts
    result = await db.execute(
        select(Alert)
        .where(
            Alert.alert_type == alert_type,
            Alert.message == message,
            Alert.resolved == False
        )
    )

    existing_alert = result.scalar_one_or_none()


    if existing_alert:
        return existing_alert


    alert = Alert(
        alert_type=alert_type,
        severity=severity,
        message=message
    )


    db.add(alert)

    await db.commit()

    await db.refresh(alert)

    return alert
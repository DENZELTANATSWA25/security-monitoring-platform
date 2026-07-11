from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert


async def create_alert(
    db: AsyncSession,
    alert_type: str,
    severity: str,
    message: str,
):
    result = await db.execute(
        select(Alert).where(
            Alert.alert_type == alert_type,
            Alert.message == message,
            Alert.resolved.is_(False)
        )
    )

    existing_alert = result.scalar_one_or_none()

    if existing_alert:
        existing_alert.severity = severity
        existing_alert.message = message
        existing_alert.created_at = func.now()

        await db.commit()
        await db.refresh(existing_alert)

        return existing_alert

    alert = Alert(
        alert_type=alert_type,
        severity=severity,
        message=message,
        resolved=False,
    )

    db.add(alert)
    await db.commit()
    await db.refresh(alert)

    return alert

async def get_alerts(
        db: AsyncSession,
):
    result = await db.execute(
        select(Alert)
        .order_by(Alert.created_at.desc())
    )

    return result.scalars().all()

async def get_alert_by_id(
    db: AsyncSession,
    alert_id: int
):
    result = await db.execute(
        select(Alert)
        .where(Alert.id == alert_id)
    )

    return result.scalar_one_or_none()

async def resolve_alert(
    db: AsyncSession,
    alert_id: int
):
    alert = await get_alert_by_id(
        db,
        alert_id
    )

    if not alert:
        return None

    alert.resolved = True


    await db.commit()
    await db.refresh(alert)

    return alert
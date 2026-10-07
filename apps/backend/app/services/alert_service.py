"""Service layer for security alerts."""

from datetime import datetime

from sqlalchemy import asc, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.alert import Alert


async def create_alert(
    db: AsyncSession,
    alert_type: str,
    severity: str,
    message: str
) -> Alert:
    """
    Create a new alert or update an existing unresolved alert.

    This function deliberately does not commit the transaction.
    Transaction ownership belongs to the calling workflow so that alerts
    can be persisted atomically with the operation that generated them.
    """

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

        await db.flush()
        return existing_alert

    alert = Alert(
        alert_type=alert_type,
        severity=severity,
        message=message,
        resolved=False,
    )

    db.add(alert)
    await db.flush()

    return alert

async def get_alerts(
        db: AsyncSession,
        *,
        limit: int = 50,
        offset: int = 0,
        resolved: bool | None= None,
        severity: str | None = None,
        alert_type: str | None = None,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        search: str | None = None,
        sort_order: str = "desc",
) -> list[Alert]:
    """Return filtered and paginated security alerts."""

    query = select(Alert)

    if resolved is not None:
        query = query.where(
            Alert.resolved.is_(resolved)
        )

    if severity is not None:
        query = query.where(
            Alert.severity == severity
        )

    if alert_type is not None:
        query = query.where(
            Alert.alert_type == alert_type
        )

    if start_date is not None:
        query = query.where(
            Alert.created_at >= start_date
        )

    if end_date is not None:
        query = query.where(
            Alert.created_at <= end_date
        )

    if search:
        search_term = f"%{search.strip()}%"

        query = query.where(
            or_(
                Alert.alert_type.ilike(search_term),
                Alert.severity.ilike(search_term),
                Alert.message.ilike(search_term),
            )
        )

    order_function = (
        asc
        if sort_order == "asc"
        else desc
    )

    query= (
        query
        .order_by(
            order_function(Alert.created_at),
            order_function(Alert.id),
        )
        .offset(offset)
        .limit(limit)
    )

    result =  await db.execute(query)

    return list(result.scalars().all())


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
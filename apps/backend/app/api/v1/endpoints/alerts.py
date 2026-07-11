from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

from app.schemas.alert import AlertResponse

from app.services.alert_service import (
    get_alerts,
    get_alert_by_id,
    resolve_alert
)

router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"]
)

@router.get(
    "/",
    response_model=list[AlertResponse]
)
async def list_alerts(
    db: AsyncSession = Depends(get_db),
):
    return await get_alerts(db)


@router.get(
    "/{alert_id}",
    response_model=AlertResponse
)
async def read_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
):
    alert = await get_alert_by_id(db, alert_id)

    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Alert not found"
        )
    return alert

@router.patch(
    "/{alert_id}/resolve",
    response_model=AlertResponse
)
async def mark_resolved(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
):
    alert = await resolve_alert(db, alert_id)

    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Alert not found"
        )

    return alert

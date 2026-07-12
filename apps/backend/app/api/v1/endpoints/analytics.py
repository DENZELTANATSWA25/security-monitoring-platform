from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.analytics_service import (
    get_event_trend as get_event_trend_service
)

router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"]
)

@router.get("/events")
async def get_event_trend(
    db: AsyncSession = Depends(get_db),
):
    return await get_event_trend_service(db)
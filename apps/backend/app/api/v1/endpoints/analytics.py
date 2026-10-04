"""Endpoints for security analytics."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.analytics import EventTrendItem
from app.services.analytics_service import (
    get_event_trend as get_event_trend_service,
)


router = APIRouter(
    prefix="/analytics",
    tags=["Analytics"],
)


@router.get(
    "/events",
    response_model=list[EventTrendItem],
)
async def get_event_trend(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return event counts grouped by calendar date."""

    return await get_event_trend_service(db)
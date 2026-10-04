"""Endpoints for querying security events."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.user import User
from app.schemas.security_event import SecurityEventListResponse
from app.services.event_query_service import get_all_events


router = APIRouter(
    prefix="/events",
    tags=["Security Events"],
)


@router.get(
    "/",
    response_model=list[SecurityEventListResponse],
)
async def list_security_events(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return security events to an authenticated user."""

    return await get_all_events(db)
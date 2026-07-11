from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

from app.schemas.security_event import (
    SecurityEventCreate,
    SecurityEventResponse,
    SecurityEventListResponse
)
from app.services.event_query_service import get_all_events
from app.services.event_service import create_event

from app.models.user import User

from app.core.dependencies import get_current_user
from typing import List


router = APIRouter(
    prefix="/events",
    tags=["Security Events"]
)


@router.post(
    "/",
    response_model=SecurityEventResponse
)
async def create_security_event(
    event: SecurityEventCreate,
    db: AsyncSession = Depends(get_db)
):

    return await create_event(
        db,
        event
    )


@router.get(
    "/",
    response_model=List[SecurityEventListResponse]
)
async def list_security_events(
    db: AsyncSession = Depends(get_db),
):
    return await get_all_events(db)
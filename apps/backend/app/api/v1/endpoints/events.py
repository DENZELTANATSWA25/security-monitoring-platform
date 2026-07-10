from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

from app.schemas.security_event import (
    SecurityEventCreate,
    SecurityEventResponse
)

from app.services.event_service import create_event

from app.models.user import User

from app.core.dependencies import get_current_user


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
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):

    event.user_id = current_user.id

    return await create_event(
        db,
        event
    )
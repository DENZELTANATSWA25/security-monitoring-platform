from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.permissions import require_role

from app.db.session import get_db

from app.models.user import (
    User,
    UserRole
)

from app.schemas.user import UserResponse

from app.services.user_service import get_all_users

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)


@router.get(
        "/"
        , response_model=list[UserResponse]
)
async def list_users(
        db: AsyncSession = Depends(get_db),
        _: User = Depends(
            require_role(UserRole.ADMIN)
        ),
):
    return await get_all_users(db)

@router.get(
    "/me",
    response_model=UserResponse
)
async def read_users_me(
    current_user: User = Depends(get_current_user),
):
    return current_user
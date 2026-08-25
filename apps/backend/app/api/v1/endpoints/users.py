from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.permissions import require_role

from app.db.session import get_db

from app.models.user import (
    User,
    UserRole,
)

from app.schemas.user import (
    UserResponse,
    UserRoleUpdate,
    UserStatusUpdate,
    UserVerificationUpdate,
)

from app.services.user_service import (
    get_all_users,
    get_user_by_id,
    update_user_role,
    update_user_status,
    update_user_verification,
)


router = APIRouter(
    prefix="/users",
    tags=["Users"],
)


@router.get(
    "/",
    response_model=list[UserResponse],
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
    response_model=UserResponse,
)
async def read_users_me(
    current_user: User = Depends(get_current_user),
):
    return current_user


@router.get(
    "/{user_id}",
    response_model=UserResponse,
)
async def read_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(
        require_role(UserRole.ADMIN)
    ),
):
    user = await get_user_by_id(
        db,
        user_id
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    return user


@router.patch(
    "/{user_id}/role",
    response_model=UserResponse,
)
async def change_user_role(
    user_id: int,
    payload: UserRoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.ADMIN)
    ),
):
    if current_user.id == user_id:
        raise HTTPException(
            status_code=400,
            detail="You cannot change your own role",
        )

    user = await update_user_role(
        db,
        user_id,
        payload.role,
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    return user


@router.patch(
    "/{user_id}/status",
    response_model=UserResponse,
)
async def change_user_status(
    user_id: int,
    payload: UserStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.ADMIN)
    ),
):
    if current_user.id == user_id:
        raise HTTPException(
            status_code=400,
            detail="You cannot deactivate your own account",
        )

    user = await update_user_status(
        db,
        user_id,
        payload.is_active,
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    return user


@router.patch(
    "/{user_id}/verification",
    response_model=UserResponse,
)
async def change_user_verification(
    user_id: int,
    payload: UserVerificationUpdate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(
        require_role(UserRole.ADMIN)
    ),
):
    user = await update_user_verification(
        db,
        user_id,
        payload.is_verified,
    )

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found",
        )

    return user
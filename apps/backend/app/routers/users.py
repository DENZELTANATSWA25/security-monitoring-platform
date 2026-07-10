from fastapi import APIRouter, Depends

from app.models.user import User
from app.schemas.user import UserResponse
from app.core.dependencies import get_current_user
from app.core.permissions import require_role
from app.models.user import UserRole

router = APIRouter(
    prefix="/users",
    tags=["Users"]
)

@router.get(
    "/me",
    response_model=UserResponse
)
async def get_profile(
    current_user: User = Depends(get_current_user)
):
    return current_user 

@router.get("/admin")
async def admin_only(
    current_user: User = Depends(
        require_role(UserRole.ADMIN)
    )
):
    return {
        "message": "Welcome, Admin!",
        "user": current_user.username
    }


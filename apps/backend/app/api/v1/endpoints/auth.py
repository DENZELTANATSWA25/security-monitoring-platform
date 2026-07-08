from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.user import (
    UserCreate,
    UserLogin,
    UserResponse,
    Token
)

from app.services.auth_service import login_user

from app.services.user_service import create_user

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

@router.post(
    "/register",
    response_model=UserResponse
)
async def register_user(
    user: UserCreate,
    db:AsyncSession = Depends(get_db)
):
    try:
        return await create_user(db, user)
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )
    
@router.post(
    "/login",
    response_model=Token
)
async def login(
    user: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    try:
        return await login_user(
            db,
            user.email,
            user.password
        )
    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e)
        )
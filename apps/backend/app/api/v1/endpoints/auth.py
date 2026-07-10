from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_role
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.user import User, UserRole
from app.schemas.user import (
    Token,
    UserCreate,
    UserLogin,
    UserResponse,
)
from app.services.audit_service import log_event
from app.services.auth_service import login_user
from app.services.user_service import create_user
from app.services.login_attempt_service import (
    record_login_attempt,
    count_failed_attempts
)

from app.models.security_event import EventSeverity
from app.schemas.security_event import SecurityEventCreate
from app.services.event_service import create_event

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
)
async def register_user(
    user: UserCreate,
    db: AsyncSession = Depends(get_db),
):
    try:
        new_user = await create_user(db, user)

        await log_event(
            db=db,
            action="REGISTER",
            resource="USER",
            user_id=new_user.id,
            details=f"{new_user.email} registered",
        )

        return new_user

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e),
        )


@router.post(
    "/login",
    response_model=Token,
)
async def login(
    user: UserLogin,
    db: AsyncSession = Depends(get_db),
):
    try:
        return await login_user(
            db=db,
            email=user.email,
            password=user.password,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=401,
            detail=str(e),
        )


@router.get("/audit")
async def get_audit_logs(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(require_role(UserRole.ADMIN)),
):
    result = await db.execute(
        select(AuditLog).order_by(AuditLog.timestamp.desc())
    )

    return result.scalars().all()
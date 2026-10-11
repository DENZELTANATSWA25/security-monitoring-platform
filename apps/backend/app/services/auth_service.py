from sqlalchemy.ext.asyncio import AsyncSession

from datetime import datetime, timezone

from app.core.security import (
    verify_password,
    create_access_token,
)

from app.services.user_service import get_user_by_email
from app.services.audit_service import log_event

from app.services.login_attempt_service import (
    record_login_attempt
)


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
):

    user = await get_user_by_email(
        db,
        email,
    )

    if not user:
        return None

    if not verify_password(
        password,
        user.hashed_password,
    ):
        return None

    return user


async def login_user(
    db: AsyncSession,
    email: str,
    password: str,
    ip_address: str | None = None,
    latitude: float | None = None,
    longitude: float | None = None,
):

    user = await authenticate_user(
        db,
        email,
        password,
    )

    # Failed login
    if not user:

        await record_login_attempt(
            db=db,
            email=email,
            successful=False,
            ip_address=ip_address,
            latitude=latitude,
            longitude=longitude,
        )

        raise ValueError(
            "Invalid email or password"
        )

    # Successful login
    await record_login_attempt(
        db=db,
        email=email,
        successful=True,
        ip_address=ip_address,
        latitude=latitude,
        longitude=longitude,
    )

    await log_event(
        db=db,
        action="LOGIN",
        resource="USER",
        user_id=user.id,
        details=f"{user.email} logged in",
    )

    # Record the latest successful authentication time.
    # The existing database column stores timezone-naive UTC values
    user.last_login = datetime.now(timezone.utc).replace(tzinfo=None)

    await db.commit()

    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role.value,
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
    }
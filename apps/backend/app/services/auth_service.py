from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    verify_password,
    create_access_token,
)

from app.services.user_service import (
    get_user_by_email
)


async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str
):

    user = await get_user_by_email(
        db,
        email
    )

    if not user:
        return None


    if not verify_password(
        password,
        user.hashed_password
    ):
        return None


    return user



async def login_user(
    db: AsyncSession,
    email: str,
    password: str
):

    user = await authenticate_user(
        db,
        email,
        password
    )


    if not user:
        raise ValueError(
            "Invalid email or password"
        )


    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "role": user.role.value
        }
    )


    return {
        "access_token": access_token,
        "token_type": "bearer"
    }
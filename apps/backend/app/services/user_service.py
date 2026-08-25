from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User, UserRole
from app.schemas.user import UserCreate
from app.core.security import hash_password


async def get_user_by_email(
    db: AsyncSession,
    email: str
):
    result = await db.execute(
        select(User)
        .where(User.email == email)
    )

    return result.scalar_one_or_none()

async def get_user_by_id(
    db: AsyncSession,
    user_id: int
):
    result = await db.execute(
        select(User)
        .where(User.id == user_id)
    )

    return result.scalar_one_or_none()



async def create_user(
    db: AsyncSession,
    user_data: UserCreate
):

    existing_user = await get_user_by_email(
        db,
        user_data.email
    )

    if existing_user:
        raise ValueError(
            "Email already registered"
        )


    user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=hash_password(
            user_data.password
        )
    )


    db.add(user)

    await db.commit()

    await db.refresh(user)

    return user

async def get_all_users(
        db: AsyncSession,
):
    result = await db.execute(
        select(User)
        .order_by(User.created_at.desc())
    )
    return result.scalars().all()

async def update_user_role(
        db: AsyncSession,
        user_id: int,
        role: UserRole
):
    user = await get_user_by_id(
        db,
        user_id
    )

    if not user:
        return None

    user.role = role

    await db.commit()
    await db.refresh(user)

    return user

async def update_user_status(
        db: AsyncSession,
        user_id: int,
        is_active: bool
):
    user = await get_user_by_id(
        db,
        user_id
    )

    if not user:
        return None

    user.is_active = is_active

    await db.commit()
    await db.refresh(user)

    return user

async def update_user_verification(
        db: AsyncSession,
        user_id: int,
        is_verified: bool
):
    user = await get_user_by_id(
        db,
        user_id
    )

    if not user:
        return None

    user.is_verified = is_verified

    await db.commit()
    await db.refresh(user)

    return user
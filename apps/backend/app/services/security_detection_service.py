from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta

from app.models.login_attempt import LoginAttempt


async def count_failed_attempts(
    db: AsyncSession,
    email: str
):

    five_minutes_ago = (
        datetime.utcnow()
        -
        timedelta(minutes=5)
    )

    result = await db.execute(
        select(func.count(LoginAttempt.id))
        .where(
            LoginAttempt.email == email,
            LoginAttempt.successful == False,
            LoginAttempt.timestamp > five_minutes_ago
        )
    )

    return result.scalar()
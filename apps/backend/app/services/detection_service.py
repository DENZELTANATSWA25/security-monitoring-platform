from datetime import datetime, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.login_attempt import LoginAttempt

FAILED_LOGIN_THRESHOLD = 5
TIME_WINDOW = datetime.utcnow() - timedelta(minutes=5)

async def detect_bruteforce(
    db: AsyncSession,
    user_id: int | None,
    ip: str
):
    
    result = await db.execute(
        select(func.count(LoginAttempt.id))
        .where(
            LoginAttempt.ip_address == ip,
            LoginAttempt.created_at > TIME_WINDOW,
            LoginAttempt.successful == False
        )
    )

    attempts = result.scalar()

    if attempts >= 5:
        return {
            "detected": True,
            "rule": "BRUTE_FORCE_LOGIN",
            "severity": "HIGH",
        }

    return {
        "detected": False
    }

import logging

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.endpoints import (
    auth,
    users,
    audit,
    events,
    alerts,
    dashboard,
    analytics,
    websocket,
    incidents,
    reports,
    ingestion,
    telemetry_sources,
    detection_rules,
)

from app.core.config import settings
from app.core.logging import configure_logging
from app.core.redis import get_redis
from app.db.session import get_db


configure_logging()

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.APP_NAME
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    auth.router,
    prefix="/api/v1"
)
app.include_router(
    users.router,
    prefix="/api/v1"
)
app.include_router(
    audit.router,
    prefix="/api/v1"
)
app.include_router(
    events.router,
    prefix="/api/v1"
)
app.include_router(
    alerts.router,
    prefix="/api/v1"
)
app.include_router(
    dashboard.router,
    prefix="/api/v1"
)
app.include_router(
    analytics.router,
    prefix="/api/v1"
)
app.include_router(
    websocket.router
)
app.include_router(
    incidents.router,
    prefix="/api/v1"
)
app.include_router(
    reports.router,
    prefix="/api/v1"
)
app.include_router(
    ingestion.router,
    prefix="/api/v1",
)
app.include_router(
    telemetry_sources.router,
    prefix="/api/v1",
)
app.include_router(
    detection_rules.router,
    prefix="/api/v1",
)

@app.get("/")
async def root() -> dict[str, str]:
    """Return basic application information."""

    return {
        "status": "ok",
        "environment": settings.APP_ENV,
        "message": "Backend is running"
    }

@app.get("/health")
async def health_check() -> dict[str, str]:
    """Report whether the application process is alive."""
    return {
        "status": "ok",
    }

@app.get("/ready")
async def readiness_check(
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> dict[str, str]:
    """Report whether required infrastructure is reachable."""

    try:
        await db.execute(
            text("SELECT 1")
        )
        await redis.ping()
    except Exception:
        logger.exception(
            "Application readiness check failed"
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service is not ready",
        ) from None

    return {
        "status": "ready",
        "database": "ok",
        "redis": "ok",
    }
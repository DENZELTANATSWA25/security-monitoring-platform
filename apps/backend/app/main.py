from fastapi import FastAPI

from app.api.v1.endpoints import auth, users, audit, events

from app.core.config import settings
from app.db.init_db import init_database
from app.db import base
from app.models import (
    user,
    audit_log,
    security_event
)


app = FastAPI(
    title=settings.APP_NAME
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


@app.on_event("startup")
async def on_startup():
    await init_database()


@app.get("/")
async def health_check():
    return {
        "status": "ok",
        "environment": settings.APP_ENV,
        "message": "Backend is running"
    }
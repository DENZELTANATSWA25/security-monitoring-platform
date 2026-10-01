from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
)

from app.core.config import settings

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


@app.get("/")
async def health_check():
    return {
        "status": "ok",
        "environment": settings.APP_ENV,
        "message": "Backend is running"
    }
from fastapi import FastAPI

from app.api.v1.endpoints import auth

from app.core.config import settings
from app.db.init_db import init_database


app = FastAPI(
    title=settings.APP_NAME
)


app.include_router(
    auth.router,
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
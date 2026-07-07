from fastapi import FastAPI

from app.core.config import settings
from app.db.init_db import init_database

app = FastAPI(title=settings.APP_NAME)

@app.on_event("startup")
def on_startup():
    init_database()

@app.get("/")
def health_check():
    return {
        "status": "ok",
        "environment": settings.APP_ENV,
        "mesage": "Backend is running"}
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

from app.schemas.dashboard import DashboardSummary

from app.services.dashboard_service import get_dashboard_summary

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"]
)

@router.get(
    "/summary",
    response_model=DashboardSummary
)
async def dashboard_summary(
    db: AsyncSession = Depends(get_db),
):
    return await get_dashboard_summary(db)
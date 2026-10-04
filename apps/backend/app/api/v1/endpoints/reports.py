from fastapi import (
    APIRouter,
    Depends
)

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db

from app.schemas.report import (
    SecurityReportResponse,
)

from app.services.report_service import (
    get_security_report,
)

from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(
    prefix="/reports",
    tags=["Reports"],
)


@router.get(
    "/security-summary",
    response_model=SecurityReportResponse
)
async def get_security_summary(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user)
):
    """Return security report data to an authenticated user."""

    return await get_security_report(db)
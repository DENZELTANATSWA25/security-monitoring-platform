"""Administrative endpoints for application audit logs."""

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_role
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.audit import AuditLogResponse
from app.services.audit_service import get_audit_logs


router = APIRouter(
    prefix="/audit",
    tags=["Audit"],
)


@router.get(
    "",
    response_model=list[AuditLogResponse],
)
async def list_audit_logs(
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=100,
        ),
    ] = 50,
    offset: Annotated[
        int,
        Query(
            ge=0,
        ),
    ] = 0,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(
        require_role(UserRole.ADMIN),
    ),
):
    """Return a paginated list of audit logs for administrators."""

    return await get_audit_logs(
        db=db,
        limit=limit,
        offset=offset,
    )

"""Administrative endpoints for application audit logs."""

from datetime import datetime
from typing import Annotated, Literal

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
    user_id: Annotated[
        int | None,
        Query(
            ge=1,
        ),
    ] = None,
    action: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=100,
        ),
    ] = None,
    resource: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=200,
        ),
    ] = None,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    search: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=200,
        ),
    ] = None,
    sort_order: Literal["asc", "desc"] = "desc",
    db: AsyncSession = Depends(get_db),
    _: User = Depends(
        require_role(UserRole.ADMIN),
    ),
):
    """Return filtered and paginated audit logs for administrators."""

    return await get_audit_logs(
        db=db,
        limit=limit,
        offset=offset,
        user_id=user_id,
        action=action,
        resource=resource,
        start_date=start_date,
        end_date=end_date,
        search=search,
        sort_order=sort_order,
    )
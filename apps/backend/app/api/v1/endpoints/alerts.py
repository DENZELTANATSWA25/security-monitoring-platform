"""Endpoints for querying and managing security alerts."""

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.core.permissions import require_role
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.alert import AlertResponse
from app.services.alert_service import (
    get_alert_by_id,
    get_alerts,
    resolve_alert,
)


router = APIRouter(
    prefix="/alerts",
    tags=["Alerts"],
)


@router.get(
    "/",
    response_model=list[AlertResponse],
)
async def list_alerts(
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    resolved: bool | None = None,
    severity: str | None = Query(
        default=None,
        min_length=1,
        max_length=50,
    ),
    alert_type: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
    ),
    start_date: datetime | None = None,
    end_date: datetime | None = None,
    search: str | None = Query(
        default=None,
        min_length=1,
        max_length=200,
    ),
    sort_order: Literal["asc", "desc"] = "desc",
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return filtered and paginated security alerts."""

    return await get_alerts(
        db,
        limit=limit,
        offset=offset,
        resolved=resolved,
        severity=severity,
        alert_type=alert_type,
        start_date=start_date,
        end_date=end_date,
        search=search,
        sort_order=sort_order,
    )


@router.get(
    "/{alert_id}",
    response_model=AlertResponse,
)
async def read_alert(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Return a single alert to an authenticated user."""

    alert = await get_alert_by_id(
        db,
        alert_id,
    )

    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Alert not found",
        )

    return alert


@router.patch(
    "/{alert_id}/resolve",
    response_model=AlertResponse,
)
async def mark_resolved(
    alert_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(
        require_role(
            UserRole.ADMIN,
            UserRole.ANALYST,
        )
    ),
):
    alert = await resolve_alert(
        db,
        alert_id,
    )

    if not alert:
        raise HTTPException(
            status_code=404,
            detail="Alert not found",
        )

    return alert
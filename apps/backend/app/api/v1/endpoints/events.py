"""Endpoints for querying security events."""

from datetime import datetime
from typing import Literal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_current_user
from app.db.session import get_db
from app.models.security_event import EventSeverity
from app.models.user import User
from app.schemas.security_event import SecurityEventListResponse
from app.services.event_query_service import get_all_events


router = APIRouter(
    prefix="/events",
    tags=["Security Events"],
)


@router.get(
    "/",
    response_model=list[SecurityEventListResponse],
)
async def list_security_events(
    limit: int = Query(
        default=50,
        ge=1,
        le=100,
    ),
    offset: int = Query(
        default=0,
        ge=0,
    ),
    severity: EventSeverity | None = None,
    event_type: str | None = Query(
        default=None,
        min_length=1,
        max_length=100,
    ),
    source: str | None = Query(
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
    """Return filtered and paginated security events."""

    return await get_all_events(
        db,
        limit=limit,
        offset=offset,
        severity=severity,
        event_type=event_type,
        source=source,
        start_date=start_date,
        end_date=end_date,
        search=search,
        sort_order=sort_order,
    )
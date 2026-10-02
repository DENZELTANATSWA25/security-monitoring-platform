"""Authentication for machine-to-machine telemetry ingestion."""

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import get_db
from app.models.telemetry_source import TelemetrySource
from app.services.telemetry_source_service import authenticate_telemetry_source


async def require_telemetry_source(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TelemetrySource:
    """
    Authenticate a registered external telemetry producer.

    Producers authenticate using their individual telemetry credential.
    Malformed, unknown, revoked, and invalid credentials are intentionally
    reported with the same response so authentication details are not leaked.
    """

    supplied_credential = request.headers.get(
        settings.INGESTION_API_KEY_HEADER,
    )

    if not supplied_credential:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing ingestion credentials",
        )

    source = await authenticate_telemetry_source(
        db=db,
        credential=supplied_credential,
    )

    if source is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid ingestion credentials",
        )

    return source

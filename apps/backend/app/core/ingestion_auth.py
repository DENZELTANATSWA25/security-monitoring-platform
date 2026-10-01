# Authentication for machine-to-machine telemetry ingestion.


import secrets
from fastapi import HTTPException, Request, status

from app.core.config import settings

async def require_ingestion_api_key(
        request: Request,
) -> None:
    """
    Authenticate an external telemetry producer.

    External agents authenticate independently from human application users.
    The configured API key is supplied through the ingestion authentication header and compared using a timing-safe comparison.
    """

    configured_key = settings.INGESTION_API_KEY

    # An unset server-side key must never make the ingestion endpoint public.
    if not configured_key:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telemetry ingestion is not configured",
        )

    supplied_key = request.headers.get(
        settings.INGESTION_API_KEY_HEADER,
    )

    if not supplied_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing ingestion credentials",
        )

    if not secrets.compare_digest(
        configured_key,
        supplied_key,
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid ingestion credentials",
        )
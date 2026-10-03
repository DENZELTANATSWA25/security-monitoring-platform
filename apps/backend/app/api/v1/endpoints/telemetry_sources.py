"""Administrative endpoints for managing telemetry sources."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_role
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.telemetry_source import (
    TelemetrySourceCreate,
    TelemetrySourceCreatedResponse,
    TelemetrySourceResponse,
    TelemetrySourceStatusResponse,
    TelemetrySourceCredentialRotatedResponse,
)
from app.services.telemetry_source_service import (
    create_telemetry_source,
    get_all_telemetry_sources,
    get_telemetry_source_by_id,
    get_telemetry_source_statuses,
    revoke_telemetry_source,
    rotate_telemetry_source_credential,
)
from app.services.audit_service import log_event


router = APIRouter(
    prefix="/telemetry-sources",
    tags=["Telemetry Sources"],
)


@router.post(
    "",
    response_model=TelemetrySourceCreatedResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register_telemetry_source(
    payload: TelemetrySourceCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.ADMIN),
    ),
):
    """Register a new telemetry producer and return its credential once."""

    try:
        source, credential = await create_telemetry_source(
            db=db,
            name=payload.name,
            source_type=payload.source_type,
        )


        await log_event(
            db=db,
            action="TELEMETRY_SOURCE_CREATED",
            resource="TELEMETRY_SOURCE",
            user_id=current_user.id,
            details=(
                f"Created telemetry source "
                f"'{source.name}' (id={source.id})"
            ),
        )

        # Source creation and its audit record become permanent together.
        await db.commit()
        await db.refresh(source)

    except IntegrityError:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A telemetry source with this name already exists",
        )

    except Exception:
        await db.rollback()

        raise

    return TelemetrySourceCreatedResponse(
        id=source.id,
        name=source.name,
        source_type=source.source_type,
        key_id=source.key_id,
        is_active=source.is_active,
        last_seen_at=source.last_seen_at,
        created_at=source.created_at,
        updated_at=source.updated_at,
        credential=credential.credential,
    )


@router.get(
    "",
    response_model=list[TelemetrySourceResponse],
)
async def list_telemetry_sources(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(
        require_role(UserRole.ADMIN),
    ),
):
    """List registered telemetry producers."""

    return await get_all_telemetry_sources(db)

@router.get(
    "/status",
    response_model=list[TelemetrySourceStatusResponse],
)
async def telemetry_source_status(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(
        require_role(
            UserRole.ADMIN,
            UserRole.ANALYST,
        )
    ),
):
    """Return operational health information for telemetry sources."""

    return await get_telemetry_source_statuses(db)


@router.post(
    "/{source_id}/rotate-credential",
    response_model=TelemetrySourceCredentialRotatedResponse,
)
async def rotate_source_credential(
    source_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.ADMIN),
    ),
):
    """Rotate a telemetry producer credential and return it once."""

    source = await get_telemetry_source_by_id(
        db=db,
        source_id=source_id,
    )

    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Telemetry source not found",
        )

    if not source.is_active:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Cannot rotate credentials for a revoked telemetry source",
        )

    try:
        source, credential = await rotate_telemetry_source_credential(
            db=db,
            source=source,
        )

        await log_event(
            db=db,
            action="TELEMETRY_SOURCE_CREDENTIAL_ROTATED",
            resource="TELEMETRY_SOURCE",
            user_id=current_user.id,
            details=(
                f"Rotated credential for telemetry source "
                f"'{source.name}' (id={source.id})"
            ),
        )

        # Rotation and its audit record become permanent together.
        await db.commit()
        await db.refresh(source)

    except Exception:
        await db.rollback()
        raise

    return TelemetrySourceCredentialRotatedResponse(
        id=source.id,
        name=source.name,
        source_type=source.source_type,
        key_id=source.key_id,
        is_active=source.is_active,
        last_seen_at=source.last_seen_at,
        created_at=source.created_at,
        updated_at=source.updated_at,
        credential=credential.credential,
    )


@router.get(
    "/{source_id}",
    response_model=TelemetrySourceResponse,
)
async def read_telemetry_source(
    source_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(
        require_role(UserRole.ADMIN),
    ),
):
    """Return one registered telemetry producer."""

    source = await get_telemetry_source_by_id(
        db=db,
        source_id=source_id,
    )

    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Telemetry source not found",
        )

    return source


@router.post(
    "/{source_id}/revoke",
    response_model=TelemetrySourceResponse,
)
async def revoke_source(
    source_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.ADMIN),
    ),
):
    """Revoke a registered telemetry producer."""

    source = await get_telemetry_source_by_id(
        db=db,
        source_id=source_id,
    )

    if source is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Telemetry source not found",
        )

    try:
        source = await revoke_telemetry_source(
            db=db,
            source=source,
        )

        await log_event(
            db=db,
            action="TELEMETRY_SOURCE_REVOKED",
            resource="TELEMETRY_SOURCE",
            user_id=current_user.id,
            details=(
                f"Revoked telemetry source "
                f"'{source.name}' (id={source.id})"
            ),
        )

        # Revocation and its audit record become permanent together.
        await db.commit()
        await db.refresh(source)

    except Exception:
        await db.rollback()
        raise

    return source
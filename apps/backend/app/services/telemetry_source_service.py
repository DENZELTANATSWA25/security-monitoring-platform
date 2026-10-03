# Service layer for registered external telemetry producers.

from datetime import datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.telemetry_credentials import (
    TelemetryCredential,
    generate_telemetry_credential,
    hash_telemetry_secret,
    parse_telemetry_credential,
    verify_telemetry_secret,
)
from app.models.telemetry_source import TelemetrySource

from app.core.config import settings
from app.models.security_event import SecurityEvent
from app.schemas.telemetry_source import (
    TelemetrySourceHealthStatus,
    TelemetrySourceStatusResponse,
)

async def create_telemetry_source(
    db: AsyncSession,
    name: str,
    source_type: str,
) -> tuple[TelemetrySource, TelemetryCredential]:
    """
    Register a new external telemetry producer.

    The plaintext credential is returned only during creation. Only its identifier and secret hash are persisted in the database.
    """

    credential = generate_telemetry_credential()

    source = TelemetrySource(
        name=name,
        source_type=source_type,
        key_id=credential.key_id,
        api_key_hash=hash_telemetry_secret(
            credential.secret,
        ),
    )

    db.add(source)
    await db.flush()
    await db.refresh(source)

    return source, credential

async def get_telemetry_source_by_key_id(
    db: AsyncSession,
    key_id: str,
) -> TelemetrySource | None:
    # Return the telemetry source associated with a key identifier.

    result = await db.execute(
        select(TelemetrySource).where(
            TelemetrySource.key_id == key_id,
        )
    )

    return result.scalar_one_or_none()

async def authenticate_telemetry_source(
    db: AsyncSession,
    credential: str,
) -> TelemetrySource | None:
    """
    Authenticate an external telemetry producer.

    Malformed, unknown, revoked, and invalid credentials all fail closed.
    """

    parsed = parse_telemetry_credential(
        credential,
    )

    if parsed is None:
        return None

    key_id, secret = parsed

    source = await get_telemetry_source_by_key_id(
        db=db,
        key_id=key_id,
    )

    if source is None:
        return None

    if not source.is_active:
        return None

    if not verify_telemetry_secret(
        secret,
        source.api_key_hash,
    ):
        return None

    return source

async def mark_telemetry_source_seen(
    db: AsyncSession,
    source: TelemetrySource,
) -> None:
    # Record successful telemetry activity for a registered producer.

    source.last_seen_at = datetime.utcnow()

    await db.flush()


async def get_telemetry_source_by_id(
    db: AsyncSession,
    source_id: int,
) -> TelemetrySource | None:
    """Return a telemetry source by its database identifier."""

    result = await db.execute(
        select(TelemetrySource).where(
            TelemetrySource.id == source_id,
        )
    )

    return result.scalar_one_or_none()


async def get_all_telemetry_sources(
    db: AsyncSession,
) -> list[TelemetrySource]:
    """Return all registered telemetry sources."""

    result = await db.execute(
        select(TelemetrySource).order_by(
            TelemetrySource.created_at.desc(),
        )
    )

    return list(result.scalars().all())


async def revoke_telemetry_source(
    db: AsyncSession,
    source: TelemetrySource,
) -> TelemetrySource:
    """Revoke a telemetry source so its credential can no longer authenticate."""

    source.is_active = False

    await db.flush()
    await db.refresh(source)

    return source

async def rotate_telemetry_source_credential(
    db: AsyncSession,
    source: TelemetrySource,
) -> tuple[TelemetrySource, TelemetryCredential]:
    """
    Replace a telemetry source's credential.

    A completely new key identifier and secret are generated.
    Only the new secret hash is persisted, causing the previous credential to become invalid immediately after the transaction is committed.
    """

    credential = generate_telemetry_credential()

    source.key_id = credential.key_id
    source.api_key_hash = hash_telemetry_secret(
        credential.secret,
    )

    await db.flush()
    await db.refresh(source)

    return source, credential


async def get_telemetry_source_statuses(
    db: AsyncSession,
) -> list[TelemetrySourceStatusResponse]:
    """
    Return operational health information for all telemetry sources.

    Event statistics are aggregated in one query to avoid issuing
    additional queries for every registered source.
    """

    now = datetime.utcnow()

    online_cutoff = now - timedelta(
        seconds=settings.TELEMETRY_SOURCE_ONLINE_THRESHOLD_SECONDS,
    )

    event_cutoff = now - timedelta(hours=24)

    event_stats = (
        select(
            SecurityEvent.telemetry_source_id.label("source_id"),
            func.count(SecurityEvent.id).
            filter(
                SecurityEvent.created_at >= event_cutoff,
            )
            .label("events_24h"),
            func.max(
                SecurityEvent.created_at,
            ).label("last_event_at"),
        )
        .where(
            SecurityEvent.telemetry_source_id.is_not(None),
        )
        .group_by(
            SecurityEvent.telemetry_source_id
        )
        .subquery()
    )

    result = await db.execute(
        select(
            TelemetrySource,
            func.coalesce(
                event_stats.c.events_24h,
                0,
            ).label("events_24h"),
            event_stats.c.last_event_at,
        )
        .outerjoin(
            event_stats,
            event_stats.c.source_id == TelemetrySource.id,
        )
        .order_by(TelemetrySource.created_at.desc())
    )

    statuses: list[TelemetrySourceStatusResponse] = []

    for source, events_24h, last_event_at in result.all():
        if not source.is_active:
            health_status = TelemetrySourceHealthStatus.REVOKED

        elif source.last_seen_at is None:
            health_status = TelemetrySourceHealthStatus.NEVER_CONNECTED

        elif source.last_seen_at >= online_cutoff:
            health_status = TelemetrySourceHealthStatus.ONLINE

        else:
            health_status = TelemetrySourceHealthStatus.OFFLINE

        statuses.append(
            TelemetrySourceStatusResponse(
                id=source.id,
                name=source.name,
                source_type=source.source_type,
                is_active=source.is_active,
                health_status=health_status,
                last_seen_at=source.last_seen_at,
                events_24h=events_24h,
                last_event_at=last_event_at,
            )
        )

    return statuses
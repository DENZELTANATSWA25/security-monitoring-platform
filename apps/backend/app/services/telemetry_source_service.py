# Service layer for registered external telemetry producers.

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.telemetry_credentials import (
    TelemetryCredential,
    generate_telemetry_credential,
    hash_telemetry_secret,
    parse_telemetry_credential,
    verify_telemetry_secret,
)
from app.models.telemetry_source import TelemetrySource

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

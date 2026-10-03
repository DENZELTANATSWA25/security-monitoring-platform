"""Tests for registered telemetry source management."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.telemetry_source import TelemetrySource
from app.services.telemetry_source_service import (
    authenticate_telemetry_source,
    create_telemetry_source,
    mark_telemetry_source_seen,
    rotate_telemetry_source_credential,
)


async def test_create_telemetry_source_stores_hash_not_secret(
    db_session: AsyncSession,
) -> None:
    """Registration must never persist the plaintext API secret."""

    source, credential = await create_telemetry_source(
        db=db_session,
        name="Linux Server Agent",
        source_type="linux-agent",
    )

    await db_session.commit()

    result = await db_session.execute(
        select(TelemetrySource).where(
            TelemetrySource.id == source.id,
        )
    )

    stored_source = result.scalar_one()

    assert stored_source.key_id == credential.key_id
    assert stored_source.api_key_hash != credential.secret
    assert credential.secret not in stored_source.api_key_hash
    assert len(stored_source.api_key_hash) == 64


async def test_valid_credential_authenticates_source(
    db_session: AsyncSession,
) -> None:
    source, credential = await create_telemetry_source(
        db=db_session,
        name="Authentication Test Source",
        source_type="test-agent",
    )

    await db_session.commit()

    authenticated_source = await authenticate_telemetry_source(
        db=db_session,
        credential=credential.credential,
    )

    assert authenticated_source is not None
    assert authenticated_source.id == source.id


async def test_invalid_secret_is_rejected(
    db_session: AsyncSession,
) -> None:
    _, credential = await create_telemetry_source(
        db=db_session,
        name="Invalid Secret Test Source",
        source_type="test-agent",
    )

    await db_session.commit()

    invalid_credential = (
        f"smp_{credential.key_id}.incorrect-secret"
    )

    authenticated_source = await authenticate_telemetry_source(
        db=db_session,
        credential=invalid_credential,
    )

    assert authenticated_source is None


async def test_unknown_key_id_is_rejected(
    db_session: AsyncSession,
) -> None:
    authenticated_source = await authenticate_telemetry_source(
        db=db_session,
        credential="smp_unknown-key-id.some-secret",
    )

    assert authenticated_source is None


async def test_inactive_source_is_rejected(
    db_session: AsyncSession,
) -> None:
    source, credential = await create_telemetry_source(
        db=db_session,
        name="Revoked Source",
        source_type="test-agent",
    )

    source.is_active = False

    await db_session.commit()

    authenticated_source = await authenticate_telemetry_source(
        db=db_session,
        credential=credential.credential,
    )

    assert authenticated_source is None


async def test_mark_source_seen_updates_timestamp(
    db_session: AsyncSession,
) -> None:
    source, _ = await create_telemetry_source(
        db=db_session,
        name="Last Seen Test Source",
        source_type="test-agent",
    )

    assert source.last_seen_at is None

    await mark_telemetry_source_seen(
        db=db_session,
        source=source,
    )

    assert source.last_seen_at is not None

async def test_rotate_telemetry_source_credential_replaces_credentials(
    db_session: AsyncSession,
) -> None:
    """Rotation must invalidate the old credential and issue a new one."""

    source, old_credential = await create_telemetry_source(
        db=db_session,
        name="Credential Rotation Source",
        source_type="test-agent",
    )

    await db_session.commit()

    old_key_id = source.key_id
    old_hash = source.api_key_hash

    source, new_credential = await rotate_telemetry_source_credential(
        db=db_session,
        source=source,
    )

    await db_session.commit()

    assert source.key_id != old_key_id
    assert source.api_key_hash != old_hash

    assert source.key_id == new_credential.key_id
    assert source.api_key_hash != new_credential.secret
    assert new_credential.secret not in source.api_key_hash

    old_authentication = await authenticate_telemetry_source(
        db=db_session,
        credential=old_credential.credential,
    )

    new_authentication = await authenticate_telemetry_source(
        db=db_session,
        credential=new_credential.credential,
    )

    assert old_authentication is None
    assert new_authentication is not None
    assert new_authentication.id == source.id

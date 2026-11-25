"""Phase 6B: telemetry ingestion security evaluation."""

from unittest.mock import AsyncMock

import pytest
from sqlalchemy import func, select

from app.core.config import settings
from app.core.redis import get_redis
from app.main import app
from app.models.security_event import SecurityEvent
from app.services.telemetry_source_service import create_telemetry_source


pytestmark = pytest.mark.asyncio

ENDPOINT = "/api/v1/ingestion/events"

PAYLOAD = {
    "event_type": "SECURITY_EVALUATION_EVENT",
    "severity": "WARNING",
    "source": "phase-6b-test-agent",
    "description": "Synthetic security evaluation event",
}


async def create_source(db_session, name):
    """Create an isolated synthetic telemetry producer."""
    source, credential = await create_telemetry_source(
        db=db_session,
        name=name,
        source_type="evaluation-agent",
    )

    return source, {
        settings.INGESTION_API_KEY_HEADER: credential.credential,
    }


async def count_source_events(db_session, source_id):
    """Count persisted events associated with one producer."""
    result = await db_session.execute(
        select(func.count(SecurityEvent.id)).where(
            SecurityEvent.telemetry_source_id == source_id
        )
    )

    return result.scalar_one()


async def test_rate_limit_boundary_and_retry_after(
    client,
    db_session,
):
    source, headers = await create_source(
        db_session,
        "Phase 6B Rate Limit Boundary",
    )

    limit = settings.INGESTION_RATE_LIMIT

    # Use a mock Redis counter to exercise the exact boundary
    # without sending hundreds of requests.
    redis = AsyncMock()
    redis.eval.side_effect = [limit, limit + 1]
    redis.ttl.return_value = 30

    app.dependency_overrides[get_redis] = lambda: redis

    try:
        allowed = await client.post(
            ENDPOINT,
            headers=headers,
            json=PAYLOAD,
        )

        rejected = await client.post(
            ENDPOINT,
            headers=headers,
            json=PAYLOAD,
        )
    finally:
        app.dependency_overrides.pop(get_redis, None)

    assert allowed.status_code == 201
    assert rejected.status_code == 429
    assert rejected.headers["Retry-After"] == "30"

    # Only the permitted request should persist an event.
    assert await count_source_events(
        db_session,
        source.id,
    ) == 1


async def test_rate_limited_request_does_not_modify_source(
    client,
    db_session,
):
    source, headers = await create_source(
        db_session,
        "Phase 6B Rejection Isolation",
    )

    original_last_seen = source.last_seen_at

    redis = AsyncMock()
    redis.eval.return_value = settings.INGESTION_RATE_LIMIT + 1
    redis.ttl.return_value = 15

    app.dependency_overrides[get_redis] = lambda: redis

    try:
        response = await client.post(
            ENDPOINT,
            headers=headers,
            json=PAYLOAD,
        )
    finally:
        app.dependency_overrides.pop(get_redis, None)

    assert response.status_code == 429
    assert await count_source_events(db_session, source.id) == 0

    await db_session.refresh(source)
    assert source.last_seen_at == original_last_seen


async def test_redis_failure_prevents_ingestion(
    client,
    db_session,
):
    source, headers = await create_source(
        db_session,
        "Phase 6B Redis Failure",
    )

    redis = AsyncMock()
    redis.eval.side_effect = ConnectionError(
        "Synthetic Redis outage"
    )

    app.dependency_overrides[get_redis] = lambda: redis

    try:
        # The existing implementation propagates Redis errors.
        # Raise the exception rather than accepting telemetry
        # without enforcing its rate limit.
        with pytest.raises(ConnectionError):
            await client.post(
                ENDPOINT,
                headers=headers,
                json=PAYLOAD,
            )
    finally:
        app.dependency_overrides.pop(get_redis, None)

    assert await count_source_events(db_session, source.id) == 0


async def test_identical_events_are_currently_accepted(
    client,
    db_session,
):
    source, headers = await create_source(
        db_session,
        "Phase 6B Replay Characterization",
    )

    first = await client.post(
        ENDPOINT,
        headers=headers,
        json=PAYLOAD,
    )

    second = await client.post(
        ENDPOINT,
        headers=headers,
        json=PAYLOAD,
    )

    assert first.status_code == 201
    assert second.status_code == 201

    # Characterization, not a claim of replay prevention.
    assert first.json()["id"] != second.json()["id"]

    assert await count_source_events(
        db_session,
        source.id,
    ) == 2

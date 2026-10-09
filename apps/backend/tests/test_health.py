"""Tests for application health and readiness endpoints."""

from httpx import AsyncClient
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession


async def test_root_returns_backend_status(
    client: AsyncClient,
) -> None:
    """The root endpoint should preserve its existing response."""

    response = await client.get("/")

    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "ok"
    assert body["message"] == "Backend is running"


async def test_health_check_returns_ok(
    client: AsyncClient,
) -> None:
    """Liveness should not depend on external infrastructure."""

    response = await client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
    }


async def test_readiness_reports_healthy_dependencies(
    client: AsyncClient,
) -> None:
    """Readiness should confirm PostgreSQL and Redis are reachable."""

    response = await client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ready",
        "database": "ok",
        "redis": "ok",
    }


async def test_readiness_returns_503_when_database_fails(
    client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch,
) -> None:
    """Database failure should make the application unready."""

    async def fail_execute(*args, **kwargs):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(
        db_session,
        "execute",
        fail_execute,
    )

    response = await client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Service is not ready",
    }


async def test_readiness_returns_503_when_redis_fails(
    client: AsyncClient,
    redis_client: Redis,
    monkeypatch,
) -> None:
    """Redis failure should make the application unready."""

    async def fail_ping(*args, **kwargs):
        raise RuntimeError("redis unavailable")

    monkeypatch.setattr(
        redis_client,
        "ping",
        fail_ping,
    )

    response = await client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {
        "detail": "Service is not ready",
    }
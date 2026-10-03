"""Shared Redis infrastructure."""

from collections.abc import AsyncIterator

from redis.asyncio import Redis

from app.core.config import settings

redis_client = Redis.from_url(
    settings.REDIS_URL,
    decode_responses=True,
)

async def get_redis() -> AsyncIterator[Redis]:
    """Provide the application's shared asynchronous Redis client."""

    yield redis_client
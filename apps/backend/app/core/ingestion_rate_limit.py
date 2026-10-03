"""Rate limiting for authenticated telemetry producers."""

from fastapi import Depends, HTTPException, status
from redis.asyncio import Redis

from app.core.config import settings
from app.core.ingestion_auth import require_telemetry_source
from app.core.redis import get_redis
from app.models.telemetry_source import TelemetrySource

"""
Redis execludes Lua scripts atomically. This prevents a rate-limit key from
being created without an expiry if the application stops between commands.
"""
_RATE_LIMIT_SCRIPT = """
local count = redis.call('INCR', KEYS[1])

if count == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end

return count
"""


async def require_ingestion_rate_limit(
    telemetry_source: TelemetrySource = Depends(
        require_telemetry_source
    ),
    redis: Redis = Depends(get_redis),
) -> TelemetrySource:
    """
    Enforce a fixed-window ingestion limit per telemetry source.

    Redis provides shared state so the limit remains effective when the
    application runs across multiple workers or instances.
    """

    key = (
        f"ingestion:rate-limit:"
        f"{telemetry_source.id}"
    )

    count = await redis.eval(
        _RATE_LIMIT_SCRIPT,
        1,
        key,
        settings.INGESTION_RATE_WINDOW_SECONDS,
    )

    if count > settings.INGESTION_RATE_LIMIT:
        ttl = await redis.ttl(key)

        #Defensive fallback if the key unexpectedly has no expiry.
        retry_after = (
            ttl
            if ttl > 0
            else settings.INGESTION_RATE_WINDOW_SECONDS
        )

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Telemetry ingestion rate limit exceeded",
            headers={
                "Retry-After": str(retry_after),
            },
        )

    return telemetry_source
"""Rate limiting for interactive Authentication."""

import hashlib

from fastapi import Depends, HTTPException, Request, status
from redis.asyncio import Redis

from app.core.config import settings
from app.core.redis import get_redis
from app.services.client_ip_service import get_client_ip

_RATE_LIMIT_SCRIPT = """
local email_count = redis.call('INCR', KEYS[1])

if email_count == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end

local ip_count = redis.call('INCR', KEYS[2])

if ip_count == 1 then
    redis.call('EXPIRE', KEYS[2], ARGV[1])
end

return {email_count, ip_count}
"""

def _email_rate_limit_key(
        email: str,
) -> str:
    """Build a non-plaintext Redis key for an email address

    Hashing prevents email addresses from appearing directly in Redis keys.
    """

    normalized_email = email.strip().lower()

    email_digest = hashlib.sha256(
        normalized_email.encode("utf-8")
    ).hexdigest()

    return (
        "auth:login:rate-limit:"
        f"{email_digest}"
    )

def _ip_rate_limit_key(
        ip_address: str | None,
) -> str:
    """Build the Redis rate-limit key for a client IP."""

    return (
        "auth:login:rate-limit:"
        f"{ip_address or 'unknown'}"
    )

async def require_login_rate_limit(
    request: Request,
    redis: Redis = Depends(get_redis),
) -> None:
    """
    Limit login requests by both account identifier and client IP.

    The request body is read without consuming it permanently because Starlette caches the body after the first read.
    """

    try:
        body = await request.json()
    except ValueError:
        return

    email = body.get("email")

    if not isinstance(email, str) or not email.strip():
        return

    client_ip = get_client_ip(request)

    counts = await redis.eval(
        _RATE_LIMIT_SCRIPT,
        2,
        _email_rate_limit_key(email),
        _ip_rate_limit_key(client_ip),
        settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS,
    )

    email_count = int(counts[0])
    ip_count = int(counts[1])

    if (
        email_count > settings.LOGIN_RATE_LIMIT_PER_EMAIL
        or ip_count > settings.LOGIN_RATE_LIMIT_PER_IP
    ):
        email_ttl = await redis.ttl(
            _email_rate_limit_key(email)
        )
        ip_ttl = await redis.ttl(
            _ip_rate_limit_key(client_ip)
        )

        retry_after = max(
            email_ttl,
            ip_ttl,
            1,
        )

        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many login attempts. Try again later.",
            headers={
                "Retry-After": str(retry_after),
            },
        )
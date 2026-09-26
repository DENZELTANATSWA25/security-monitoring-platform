"""Security utilities for password hashing and JWT handling."""

from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


def hash_password(password: str) -> str:
    """
    Hash a plaintext password using bcrypt.

    A new random salt is generated for every password so identical
    passwords do not produce identical stored hashes.
    """
    password_bytes = password.encode("utf-8")

    hashed_password = bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt(),
    )

    return hashed_password.decode("utf-8")


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    """Verify a plaintext password against a stored bcrypt hash."""

    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8"),
        )
    except (ValueError, TypeError):
        # A malformed stored hash must fail authentication rather than
        # causing the login endpoint to return an internal server error.
        return False


def create_access_token(data: dict) -> str:
    """Create a signed JWT access token."""

    to_encode = data.copy()

    expire = (
        datetime.now(timezone.utc)
        + timedelta(minutes=settings.JWT_EXPIRE_MINUTES)
    )

    to_encode["exp"] = expire

    return jwt.encode(
        to_encode,
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def decode_access_token(token: str):
    """Decode and validate a JWT access token."""

    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError:
        return None

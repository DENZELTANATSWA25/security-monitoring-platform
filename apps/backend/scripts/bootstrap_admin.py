"""Securely bootstrap the first administrator account."""

import asyncio
import getpass

from pydantic import EmailStr, TypeAdapter, ValidationError

from sqlalchemy import or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.db.session import AsyncSessionLocal
from app.models.user import User, UserRole


async def create_initial_admin(
    db: AsyncSession,
    *,
    email: str,
    username: str,
    full_name: str,
    password: str,
) -> User:
    """Create the initial administrator if none exists."""

    # Serialize bootstrap attempts within the same PostgreSQL database.
    # The lock is released automatically when the transaction ends.

    await db.execute(
        text("SELECT pg_advisory_xact_lock(20261011, 1)")
    )
    existing_admin = await db.scalar(
        select(User.id)
        .where(User.role == UserRole.ADMIN)
        .limit(1)
    )

    if existing_admin is not None:
        raise ValueError(
            "An administrator already exists. "
            "Bootstrap is only available for initial setup."
        )

    existing_account = await db.scalar(
        select(User.id)
        .where(
            or_(
                User.email == email,
                User.username == username,
            )
        )
        .limit(1)
    )

    if existing_account is not None:
        raise ValueError(
            "An account with that email or username already exists."
        )

    admin = User(
        email=email,
        username=username,
        full_name=full_name,
        hashed_password=hash_password(password),
        role=UserRole.ADMIN,
        is_active=True,
        is_verified=True,
    )

    db.add(admin)
    await db.flush()

    return admin


def prompt_credentials() -> dict[str, str]:
    """Collect initial administrator credentials interactively."""

    print("\nSecurity Monitoring Platform — Administrator Setup\n")

    email = input("Email: ").strip().lower()
    username = input("Username: ").strip()
    full_name = input("Full name: ").strip()

    if not email or not username or not full_name:
        raise ValueError("All account fields are required.")

    try:
        email = str(TypeAdapter(EmailStr).validate_python(email))
    except ValidationError:
        raise ValueError("Enter a valid email address.") from None

    if not 3 <= len(username) <= 100:
        raise ValueError(
            "Username must contain between 3 and 100 characters."
        )

    if len(full_name) > 255:
        raise ValueError(
            "Full name must not exceed 255 characters."
        )

    password = getpass.getpass("Password: ")
    confirmation = getpass.getpass("Confirm password: ")

    if password != confirmation:
        raise ValueError("Passwords do not match.")

    if len(password) < 12:
        raise ValueError(
            "Administrator password must contain at least 12 characters."
        )

    if len(password.encode("utf-8")) > 72:
        raise ValueError(
            "Administrator password must not exceed 72 UTF-8 bytes."
        )

    return {
        "email": email,
        "username": username,
        "full_name": full_name,
        "password": password,
    }


async def main() -> None:
    """Run the administrator bootstrap process."""

    credentials = prompt_credentials()

    async with AsyncSessionLocal() as db:
        try:
            await create_initial_admin(db, **credentials)
            await db.commit()
        except Exception:
            await db.rollback()
            raise

    print("\nAdministrator account created successfully.")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (ValueError, EOFError, KeyboardInterrupt) as exc:
        if isinstance(exc, ValueError):
            print(f"\nSetup failed: {exc}")
        else:
            raise SystemExit(1) from None
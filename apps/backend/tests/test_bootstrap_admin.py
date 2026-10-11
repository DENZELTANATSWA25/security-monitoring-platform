"""Tests for secure initial administrator provisioning."""

import pytest
from sqlalchemy import select
import asyncio

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.security import verify_password
from app.models.user import User, UserRole
from scripts.bootstrap_admin import create_initial_admin


pytestmark = pytest.mark.asyncio


async def test_bootstrap_creates_active_verified_admin(db_session):
    """Initial setup creates an administrator with a hashed password."""

    admin = await create_initial_admin(
        db_session,
        email="bootstrap@example.com",
        username="bootstrap_admin",
        full_name="Bootstrap Administrator",
        password="SecureBootstrapPassword123!",
    )

    assert admin.id is not None
    assert admin.role == UserRole.ADMIN
    assert admin.is_active is True
    assert admin.is_verified is True
    assert admin.hashed_password != "SecureBootstrapPassword123!"
    assert verify_password(
        "SecureBootstrapPassword123!",
        admin.hashed_password,
    )


async def test_bootstrap_rejects_existing_administrator(db_session):
    """A second administrator cannot be provisioned through bootstrap."""

    await create_initial_admin(
        db_session,
        email="first@example.com",
        username="first_admin",
        full_name="First Administrator",
        password="SecureBootstrapPassword123!",
    )

    with pytest.raises(ValueError, match="administrator already exists"):
        await create_initial_admin(
            db_session,
            email="second@example.com",
            username="second_admin",
            full_name="Second Administrator",
            password="SecureBootstrapPassword456!",
        )

    admins = (
        await db_session.scalars(
            select(User).where(User.role == UserRole.ADMIN)
        )
    ).all()

    assert len(admins) == 1


@pytest.mark.parametrize(
    ("email", "username"),
    [
        ("viewer@example.com", "different_username"),
        ("different@example.com", "existing_viewer"),
    ],
)
async def test_bootstrap_rejects_duplicate_account(
    db_session,
    email,
    username,
):
    """Existing account identifiers cannot be reused."""

    existing_user = User(
        email="viewer@example.com",
        username="existing_viewer",
        full_name="Existing Viewer",
        hashed_password="existing-hash",
        role=UserRole.VIEWER,
    )

    db_session.add(existing_user)
    await db_session.flush()

    with pytest.raises(ValueError, match="already exists"):
        await create_initial_admin(
            db_session,
            email=email,
            username=username,
            full_name="Bootstrap Administrator",
            password="SecureBootstrapPassword123!",
        )

    users = (await db_session.scalars(select(User))).all()

    assert len(users) == 1
    assert users[0].role == UserRole.VIEWER
    assert users[0].hashed_password == "existing-hash"

async def test_concurrent_bootstrap_allows_only_one_admin(
    test_database_url,
):
    """Concurrent bootstrap attempts cannot create two administrators."""

    engine = create_async_engine(test_database_url)

    session_factory = async_sessionmaker(
        engine,
        expire_on_commit=False,
    )

    created_admin_ids = []

    async def attempt_bootstrap(number: int):
        async with session_factory() as session:
            try:
                admin = await create_initial_admin(
                    session,
                    email=f"concurrent{number}@example.com",
                    username=f"concurrent_admin_{number}",
                    full_name=f"Concurrent Administrator {number}",
                    password="SecureBootstrapPassword123!",
                )

                await session.commit()
                created_admin_ids.append(admin.id)

                return "created"

            except ValueError:
                await session.rollback()
                return "rejected"

    try:
        results = await asyncio.gather(
            attempt_bootstrap(1),
            attempt_bootstrap(2),
        )

        assert sorted(results) == ["created", "rejected"]
        assert len(created_admin_ids) == 1

    finally:
        async with session_factory() as session:
            # Remove only the administrator created by this test.
            # Never delete unrelated accounts.
            from sqlalchemy import delete

            if created_admin_ids:
                await session.execute(
                    delete(User).where(
                        User.id.in_(created_admin_ids)
                    )
                )
                await session.commit()

        await engine.dispose()
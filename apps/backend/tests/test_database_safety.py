"""Tests for database-backed test infrastructure."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


def test_database_tests_use_test_database(
    test_database_url: str,
) -> None:
    """Database tests must use the dedicated test database."""

    assert test_database_url.endswith("/security_test_db")


async def test_database_session_can_execute_query(
    db_session: AsyncSession,
) -> None:
    """The test session can communicate with PostgreSQL."""

    result = await db_session.execute(text("SELECT 1"))

    assert result.scalar_one() == 1


async def test_database_changes_are_temporary(
    db_session: AsyncSession,
) -> None:
    """Data created during a test exists inside that test transaction."""

    await db_session.execute(
        text(
            """
            INSERT INTO login_attempts (
                email,
                successful,
                ip_address
            )
            VALUES (
                'isolation-test@example.com',
                false,
                '127.0.0.1'
            )
            """
        )
    )

    await db_session.commit()

    result = await db_session.execute(
        text(
            """
            SELECT COUNT(*)
            FROM login_attempts
            WHERE email = 'isolation-test@example.com'
            """
        )
    )

    assert result.scalar_one() == 1

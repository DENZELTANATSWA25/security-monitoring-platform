"""Shared pytest configuration and reusable test fixtures."""

from urllib.parse import urlparse

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine

from app.core.config import settings
from app.core.security import hash_password
from app.db.session import get_db
from app.main import app
from app.models.user import User, UserRole
from app.models.security_event import SecurityEvent, EventSeverity
from app.models.incident import Incident
from app.models.alert import Alert

from collections.abc import AsyncIterator
from redis.asyncio import Redis
from app.core.redis import get_redis


TEST_PASSWORD = "TestPassword123!"


def _database_name(database_url: str) -> str:
    """Extract the database name from a SQLAlchemy database URL."""
    return urlparse(database_url).path.lstrip("/")


@pytest.fixture(scope="session")
def test_database_url() -> str:
    """Ensure database tests only use the dedicated test database."""

    database_url = settings.DATABASE_URL
    database_name = _database_name(database_url)

    if database_name != "security_test_db":
        pytest.fail(
            "Database test safety check failed: "
            f"expected 'security_test_db', got '{database_name}'."
        )

    return database_url

@pytest.fixture
async def redis_client() -> AsyncIterator[Redis]:
    """
    Provide an isolated Redis database for each test.

    Redis database 1 is reserved for automated tests. The database is
    cleared before and after each test so rate-limit state cannot leak
    between tests.
    """

    client = Redis.from_url(
        settings.REDIS_URL,
        db=1,
        decode_responses=True,
    )

    await client.flushdb()

    try:
        yield client
    finally:
        await client.flushdb()
        await client.aclose()


@pytest.fixture
async def db_session(
    test_database_url: str,
) -> AsyncSession:
    """Give each test an isolated database transaction."""

    engine = create_async_engine(
        test_database_url,
        echo=False,
    )

    async with engine.connect() as connection:
        transaction = await connection.begin()

        session = AsyncSession(
            bind=connection,
            expire_on_commit=False,
            join_transaction_mode="create_savepoint",
        )

        try:
            yield session
        finally:
            await session.close()
            await transaction.rollback()

    await engine.dispose()


@pytest.fixture
async def client(
    db_session: AsyncSession,
    redis_client: Redis,
) -> AsyncClient:
    """Provide an HTTP client using the isolated test database."""

    async def override_get_db():
        yield db_session

    async def override_get_redis():
        yield redis_client

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = override_get_redis

    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as test_client:
        yield test_client

    app.dependency_overrides.clear()


async def _create_test_user(
    db_session: AsyncSession,
    *,
    email: str,
    username: str,
    full_name: str,
    role: UserRole,
) -> User:
    """Create a temporary user for an automated test."""

    user = User(
        email=email,
        username=username,
        full_name=full_name,
        hashed_password=hash_password(TEST_PASSWORD),
        role=role,
        is_active=True,
        is_verified=True,
    )

    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    return user


@pytest.fixture
async def admin_user(
    db_session: AsyncSession,
) -> User:
    """Create a temporary administrator."""

    return await _create_test_user(
        db_session,
        email="admin@example.com",
        username="test_admin",
        full_name="Test Administrator",
        role=UserRole.ADMIN,
    )


@pytest.fixture
async def analyst_user(
    db_session: AsyncSession,
) -> User:
    """Create a temporary analyst."""

    return await _create_test_user(
        db_session,
        email="analyst@example.com",
        username="test_analyst",
        full_name="Test Analyst",
        role=UserRole.ANALYST,
    )


@pytest.fixture
async def viewer_user(
    db_session: AsyncSession,
) -> User:
    """Create a temporary viewer."""

    return await _create_test_user(
        db_session,
        email="viewer@example.com",
        username="test_viewer",
        full_name="Test Viewer",
        role=UserRole.VIEWER,
    )


async def _login(
    client: AsyncClient,
    *,
    email: str,
) -> str:
    """Authenticate a test user through the real login endpoint."""

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": TEST_PASSWORD,
        },
    )

    assert response.status_code == 200

    return response.json()["access_token"]


@pytest.fixture
async def admin_token(
    client: AsyncClient,
    admin_user: User,
) -> str:
    return await _login(
        client,
        email=admin_user.email,
    )


@pytest.fixture
async def analyst_token(
    client: AsyncClient,
    analyst_user: User,
) -> str:
    return await _login(
        client,
        email=analyst_user.email,
    )


@pytest.fixture
async def viewer_token(
    client: AsyncClient,
    viewer_user: User,
) -> str:
    return await _login(
        client,
        email=viewer_user.email,
    )


@pytest.fixture
async def admin_client(
    client: AsyncClient,
    admin_token: str,
) -> AsyncClient:
    client.headers["Authorization"] = f"Bearer {admin_token}"
    return client


@pytest.fixture
async def analyst_client(
    client: AsyncClient,
    analyst_token: str,
) -> AsyncClient:
    client.headers["Authorization"] = f"Bearer {analyst_token}"
    return client


@pytest.fixture
async def viewer_client(
    client: AsyncClient,
    viewer_token: str,
) -> AsyncClient:
    client.headers["Authorization"] = f"Bearer {viewer_token}"
    return client

@pytest.fixture
async def security_event(
    db_session: AsyncSession,
) -> SecurityEvent:
    """Create a temporary security event that incidents can reference."""

    event = SecurityEvent(
        event_type="TEST_SECURITY_EVENT",
        severity=EventSeverity.WARNING,
        source="pytest",
        message="Automated test security event",
        user_id=None,
        event_metadata={
            "environment": "test",
        },
    )

    db_session.add(event)
    await db_session.commit()
    await db_session.refresh(event)

    return event

@pytest.fixture
async def incident(
    db_session: AsyncSession,
    security_event: SecurityEvent,
) -> Incident:
    """Create a temporary OPEN incident for testing"""

    incident = Incident(
        title="Test Investigation",
        description="Incident created by the automated test suite.",
        severity="HIGH",
        event_id=security_event.id,
    )
    

    db_session.add(incident)
    await db_session.commit()
    await db_session.refresh(incident)

    return incident

@pytest.fixture
async def alert(
    db_session: AsyncSession,
) -> Alert:
    """Create a temporary alert for incident-linking tests."""

    alert = Alert(
        alert_type="BRUTE_FORCE",
        severity="HIGH",
        message="Repeated failed authentication attempts",
        resolved=False,
    )

    db_session.add(alert)
    await db_session.commit()
    await db_session.refresh(alert)

    return alert

@pytest.fixture
async def additional_security_event(
    db_session: AsyncSession,
) -> SecurityEvent:
    """Create an event that may be linked during an investigation."""

    event = SecurityEvent(
        event_type="SUSPICIOUS_LOGIN",
        severity=EventSeverity.CRITICAL,
        source="pytest-secondary",
        message="Suspicious login from an unusual source.",
        user_id=None,
        event_metadata={
            "environment": "test",
            "purpose": "incident-link"
        },
    )

    db_session.add(event)
    await db_session.commit()
    await db_session.refresh(event)

    return event
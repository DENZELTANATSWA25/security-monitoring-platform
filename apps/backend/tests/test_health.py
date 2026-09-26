"""Tests for the application's health endpoint."""

from httpx import AsyncClient


async def test_health_check_returns_ok(
    client: AsyncClient,
) -> None:
    """The health endpoint should report that the backend is running."""

    # Act
    response = await client.get("/")

    # Assert
    assert response.status_code == 200

    body = response.json()

    assert body["status"] == "ok"
    assert body["message"] == "Backend is running"

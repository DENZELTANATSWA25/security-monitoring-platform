"""Tests for the generated OpenAPI documentation."""

from httpx import AsyncClient


async def test_openapi_schema_contains_application_metadata(
    client: AsyncClient,
) -> None:
    """The generated schema should expose the public API metadata."""

    response = await client.get("/openapi.json")

    assert response.status_code == 200

    schema = response.json()
    info = schema["info"]

    assert info["title"] == "Security Monitoring Platform"
    assert info["version"] == "1.0.0"
    assert "telemetry ingestion" in info["description"].lower()
    assert "incident investigation" in info["description"].lower()


async def test_openapi_schema_contains_expected_tags(
    client: AsyncClient,
) -> None:
    """The documented API groups should be present in the schema."""

    response = await client.get("/openapi.json")

    assert response.status_code == 200

    schema = response.json()

    tag_names = {
        tag["name"]
        for tag in schema["tags"]
    }

    expected_tags = {
        "Authentication",
        "Users",
        "Security Events",
        "Alerts",
        "Incidents",
        "Detection Rules",
        "Telemetry Sources",
        "Telemetry Ingestion",
        "Dashboard",
        "Analytics",
        "Reports",
        "Audit",
        "Websocket",
        "System",
    }

    assert expected_tags <= tag_names


async def test_openapi_schema_documents_system_endpoints(
    client: AsyncClient,
) -> None:
    """Infrastructure endpoints should be documented under System."""

    response = await client.get("/openapi.json")

    assert response.status_code == 200

    paths = response.json()["paths"]

    assert paths["/"]["get"]["tags"] == ["System"]
    assert paths["/health"]["get"]["tags"] == ["System"]
    assert paths["/ready"]["get"]["tags"] == ["System"]

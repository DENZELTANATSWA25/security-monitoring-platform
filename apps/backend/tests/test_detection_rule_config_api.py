"""Tests for administrative detection rule configuration."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog
from app.models.detection_rule_config import DetectionRuleConfig


async def _create_detection_rule_config(
    db_session: AsyncSession,
    *,
    rule_name: str,
    display_name: str,
    description: str = "Detection rule used by API tests.",
    is_enabled: bool = True,
) -> DetectionRuleConfig:
    """Create and persist a detection rule configuration for an API test."""

    config = DetectionRuleConfig(
        rule_name=rule_name,
        display_name=display_name,
        description=description,
        is_enabled=is_enabled,
    )

    db_session.add(config)
    await db_session.commit()
    await db_session.refresh(config)

    return config


async def test_admin_can_list_detection_rules(
    admin_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Administrators should be able to inspect detection rule configuration."""

    config = await _create_detection_rule_config(
        db_session,
        rule_name="LIST_TEST_RULE",
        display_name="List Test Rule",
    )

    response = await admin_client.get(
        "/api/v1/detection-rules",
    )

    assert response.status_code == 200

    matching_rules = [
        item
        for item in response.json()
        if item["id"] == config.id
    ]

    assert len(matching_rules) == 1

    returned_rule = matching_rules[0]

    assert returned_rule["rule_name"] == "LIST_TEST_RULE"
    assert returned_rule["display_name"] == "List Test Rule"
    assert returned_rule["is_enabled"] is True


async def test_analyst_cannot_list_detection_rules(
    analyst_client: AsyncClient,
) -> None:
    """Analysts must not have access to detection rule administration."""

    response = await analyst_client.get(
        "/api/v1/detection-rules",
    )

    assert response.status_code == 403


async def test_viewer_cannot_list_detection_rules(
    viewer_client: AsyncClient,
) -> None:
    """Viewers must not have access to detection rule administration."""

    response = await viewer_client.get(
        "/api/v1/detection-rules",
    )

    assert response.status_code == 403


async def test_unauthenticated_user_cannot_list_detection_rules(
    client: AsyncClient,
) -> None:
    """Detection rule configuration must require authentication."""

    response = await client.get(
        "/api/v1/detection-rules",
    )

    assert response.status_code == 401


async def test_admin_can_disable_detection_rule(
    admin_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Administrators should be able to disable a configured rule."""

    config = await _create_detection_rule_config(
        db_session,
        rule_name="ADMIN_DISABLE_TEST_RULE",
        display_name="Admin Disable Test Rule",
        is_enabled=True,
    )

    response = await admin_client.patch(
        f"/api/v1/detection-rules/{config.rule_name}",
        json={
            "is_enabled": False,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["rule_name"] == config.rule_name
    assert body["is_enabled"] is False

    await db_session.refresh(config)

    assert config.is_enabled is False


async def test_admin_can_enable_detection_rule(
    admin_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Administrators should be able to re-enable a configured rule."""

    config = await _create_detection_rule_config(
        db_session,
        rule_name="ADMIN_ENABLE_TEST_RULE",
        display_name="Admin Enable Test Rule",
        is_enabled=False,
    )

    response = await admin_client.patch(
        f"/api/v1/detection-rules/{config.rule_name}",
        json={
            "is_enabled": True,
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert body["rule_name"] == config.rule_name
    assert body["is_enabled"] is True

    await db_session.refresh(config)

    assert config.is_enabled is True


async def test_analyst_cannot_update_detection_rule(
    analyst_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Analysts must not be allowed to change detection configuration."""

    config = await _create_detection_rule_config(
        db_session,
        rule_name="ANALYST_UPDATE_TEST_RULE",
        display_name="Analyst Update Test Rule",
    )

    response = await analyst_client.patch(
        f"/api/v1/detection-rules/{config.rule_name}",
        json={
            "is_enabled": False,
        },
    )

    assert response.status_code == 403

    await db_session.refresh(config)

    assert config.is_enabled is True


async def test_viewer_cannot_update_detection_rule(
    viewer_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Viewers must not be allowed to change detection configuration."""

    config = await _create_detection_rule_config(
        db_session,
        rule_name="VIEWER_UPDATE_TEST_RULE",
        display_name="Viewer Update Test Rule",
    )

    response = await viewer_client.patch(
        f"/api/v1/detection-rules/{config.rule_name}",
        json={
            "is_enabled": False,
        },
    )

    assert response.status_code == 403

    await db_session.refresh(config)

    assert config.is_enabled is True


async def test_unauthenticated_user_cannot_update_detection_rule(
    client: AsyncClient,
) -> None:
    """Changing detection rule configuration must require authentication."""

    response = await client.patch(
        "/api/v1/detection-rules/ANY_RULE",
        json={
            "is_enabled": False,
        },
    )

    assert response.status_code == 401


async def test_updating_unknown_detection_rule_returns_404(
    admin_client: AsyncClient,
) -> None:
    """Updating an unknown detection rule should return not found."""

    response = await admin_client.patch(
        "/api/v1/detection-rules/UNKNOWN_TEST_RULE",
        json={
            "is_enabled": False,
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Detection rule not found"


async def test_updating_detection_rule_creates_audit_log(
    admin_client: AsyncClient,
    db_session: AsyncSession,
) -> None:
    """Configuration changes should leave an administrative audit record."""

    config = await _create_detection_rule_config(
        db_session,
        rule_name="AUDIT_TEST_RULE",
        display_name="Audit Test Rule",
        is_enabled=True,
    )

    response = await admin_client.patch(
        f"/api/v1/detection-rules/{config.rule_name}",
        json={
            "is_enabled": False,
        },
    )

    assert response.status_code == 200

    result = await db_session.execute(
        select(AuditLog).where(
            AuditLog.action
            == "DETECTION_RULE_CONFIGURATION_UPDATED",
            AuditLog.resource == "DETECTION_RULE",
        )
    )

    audit_log = result.scalar_one()

    assert audit_log.user_id is not None
    assert config.rule_name in audit_log.details
    assert "True" in audit_log.details
    assert "False" in audit_log.details


async def test_detection_rule_update_rolls_back_when_audit_fails(
    admin_client: AsyncClient,
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """
    Detection rule configuration and its audit record must be atomic.

    If audit logging fails, the original enabled state must remain persisted.
    """

    config = await _create_detection_rule_config(
        db_session,
        rule_name="ATOMICITY_TEST_RULE",
        display_name="Atomicity Test Rule",
        is_enabled=True,
    )

    config_id = config.id

    async def failing_log_event(*args, **kwargs):
        raise RuntimeError("Simulated audit failure")

    monkeypatch.setattr(
        "app.api.v1.endpoints.detection_rules.log_event",
        failing_log_event,
    )

    with pytest.raises(
        RuntimeError,
        match="Simulated audit failure",
    ):
        await admin_client.patch(
            f"/api/v1/detection-rules/{config.rule_name}",
            json={
                "is_enabled": False,
            },
        )

    await db_session.rollback()

    result = await db_session.execute(
        select(DetectionRuleConfig).where(
            DetectionRuleConfig.id == config_id,
        )
    )

    stored_config = result.scalar_one()

    assert stored_config.is_enabled is True

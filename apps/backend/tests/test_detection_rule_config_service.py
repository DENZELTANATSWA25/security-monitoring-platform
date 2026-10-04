"""Tests for persisted detection rule configuration."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.detection_rule_config import DetectionRuleConfig
from app.services.detection_rule_config_service import (
    get_detection_rule_config_by_name,
    get_detection_rule_configs,
    is_detection_rule_enabled,
    set_detection_rule_enabled,
    update_detection_rule_config,
)

import pytest
from pydantic import ValidationError


async def test_get_detection_rule_config_by_name(
    db_session: AsyncSession,
) -> None:
    """A persisted rule configuration should be retrievable by rule name."""

    config = DetectionRuleConfig(
        rule_name="TEST_RULE",
        display_name="Test Rule",
        description="Configuration used by the service test.",
        is_enabled=True,
    )

    db_session.add(config)
    await db_session.flush()

    stored = await get_detection_rule_config_by_name(
        db=db_session,
        rule_name="TEST_RULE",
    )

    assert stored is not None
    assert stored.id == config.id
    assert stored.rule_name == "TEST_RULE"


async def test_get_detection_rule_configs(
    db_session: AsyncSession,
) -> None:
    """All persisted rule configurations should be returned."""

    first = DetectionRuleConfig(
        rule_name="FIRST_TEST_RULE",
        display_name="First Test Rule",
        description="First rule.",
        is_enabled=True,
    )

    second = DetectionRuleConfig(
        rule_name="SECOND_TEST_RULE",
        display_name="Second Test Rule",
        description="Second rule.",
        is_enabled=False,
    )

    db_session.add_all([first, second])
    await db_session.flush()

    configs = await get_detection_rule_configs(db_session)

    rule_names = {
        config.rule_name
        for config in configs
    }

    assert "FIRST_TEST_RULE" in rule_names
    assert "SECOND_TEST_RULE" in rule_names


async def test_set_detection_rule_enabled(
    db_session: AsyncSession,
) -> None:
    """A rule's enabled state should be mutable."""

    config = DetectionRuleConfig(
        rule_name="DISABLE_TEST_RULE",
        display_name="Disable Test Rule",
        description="Rule used to test configuration updates.",
        is_enabled=True,
    )

    db_session.add(config)
    await db_session.flush()

    updated = await set_detection_rule_enabled(
        db=db_session,
        config=config,
        is_enabled=False,
    )

    assert updated.is_enabled is False


async def test_enabled_rule_returns_true(
    db_session: AsyncSession,
) -> None:
    """Enabled persisted rules should be considered operational."""

    config = DetectionRuleConfig(
        rule_name="ENABLED_TEST_RULE",
        display_name="Enabled Test Rule",
        description="Enabled rule.",
        is_enabled=True,
    )

    db_session.add(config)
    await db_session.flush()

    assert await is_detection_rule_enabled(
        db=db_session,
        rule_name=config.rule_name,
    ) is True


async def test_disabled_rule_returns_false(
    db_session: AsyncSession,
) -> None:
    """Disabled persisted rules should not be considered operational."""

    config = DetectionRuleConfig(
        rule_name="DISABLED_TEST_RULE",
        display_name="Disabled Test Rule",
        description="Disabled rule.",
        is_enabled=False,
    )

    db_session.add(config)
    await db_session.flush()

    assert await is_detection_rule_enabled(
        db=db_session,
        rule_name=config.rule_name,
    ) is False


async def test_missing_rule_configuration_defaults_to_enabled(
    db_session: AsyncSession,
) -> None:
    """Unseeded Python rules should remain enabled during configuration setup."""

    assert await is_detection_rule_enabled(
        db=db_session,
        rule_name="UNSEEDED_TEST_RULE",
    ) is True


async def test_detection_rule_config_stores_parameters(
    db_session: AsyncSession,
) -> None:
    """Detection rule configuration should persist rule parameters."""

    config = DetectionRuleConfig(
        rule_name="PARAMETER_TEST_RULE",
        display_name="Parameter Test Rule",
        description="Rule used to test persisted parameters.",
        is_enabled=True,
        parameters={
            "threshold": 10,
            "window_minutes": 15,
        },
    )

    db_session.add(config)
    await db_session.flush()
    await db_session.refresh(config)

    assert config.parameters == {
        "threshold": 10,
        "window_minutes": 15,
    }


async def test_detection_rule_config_defaults_to_empty_parameters(
    db_session: AsyncSession,
) -> None:
    """Rules without configurable values should receive empty parameters."""

    config = DetectionRuleConfig(
        rule_name="NO_PARAMETER_TEST_RULE",
        display_name="No Parameter Test Rule",
        description="Rule without configurable parameters.",
        is_enabled=True,
    )

    db_session.add(config)
    await db_session.flush()
    await db_session.refresh(config)

    assert config.parameters == {}

async def test_update_detection_rule_config_updates_enabled_state_and_parameters(
    db_session: AsyncSession,
) -> None:
    """Configuration updates should persist enabled state and parameters."""

    config = DetectionRuleConfig(
        rule_name="EVENT_BURST",
        display_name="Event Burst",
        description="Detect frequent security events.",
        is_enabled=True,
        parameters={
            "event_threshold": 5,
            "window_minutes": 5,
        },
    )

    db_session.add(config)
    await db_session.flush()

    updated = await update_detection_rule_config(
        db=db_session,
        config=config,
        is_enabled=False,
        parameters={
            "event_threshold": 20,
            "window_minutes": 10,
        },
    )

    assert updated.is_enabled is False
    assert updated.parameters == {
        "event_threshold": 20,
        "window_minutes": 10,
    }


async def test_update_detection_rule_config_can_update_only_enabled_state(
    db_session: AsyncSession,
) -> None:
    """Omitted parameters should leave existing parameters unchanged."""

    parameters = {
        "event_threshold": 10,
        "window_minutes": 15,
    }

    config = DetectionRuleConfig(
        rule_name="EVENT_BURST",
        display_name="Event Burst",
        description="Detect frequent security events.",
        is_enabled=True,
        parameters=parameters,
    )

    db_session.add(config)
    await db_session.flush()

    updated = await update_detection_rule_config(
        db=db_session,
        config=config,
        is_enabled=False,
    )

    assert updated.is_enabled is False
    assert updated.parameters == parameters


async def test_update_detection_rule_config_can_update_only_parameters(
    db_session: AsyncSession,
) -> None:
    """Omitted enabled state should leave the current state unchanged."""

    config = DetectionRuleConfig(
        rule_name="BRUTE_FORCE_ATTACK",
        display_name="Brute Force",
        description="Detect repeated failed authentication attempts.",
        is_enabled=True,
        parameters={
            "failed_attempts_threshold": 5,
        },
    )

    db_session.add(config)
    await db_session.flush()

    updated = await update_detection_rule_config(
        db=db_session,
        config=config,
        parameters={
            "failed_attempts_threshold": 10,
        },
    )

    assert updated.is_enabled is True
    assert updated.parameters == {
        "failed_attempts_threshold": 10,
    }


async def test_update_detection_rule_config_rejects_invalid_parameters(
    db_session: AsyncSession,
) -> None:
    """Invalid rule parameters must not be persisted."""

    original_parameters = {
        "failed_attempts_threshold": 5,
    }

    config = DetectionRuleConfig(
        rule_name="BRUTE_FORCE_ATTACK",
        display_name="Brute Force",
        description="Detect repeated failed authentication attempts.",
        is_enabled=True,
        parameters=original_parameters,
    )

    db_session.add(config)
    await db_session.flush()

    with pytest.raises(ValidationError):
        await update_detection_rule_config(
            db=db_session,
            config=config,
            parameters={
                "failed_attempts_threshold": 0,
            },
        )

    assert config.parameters == original_parameters
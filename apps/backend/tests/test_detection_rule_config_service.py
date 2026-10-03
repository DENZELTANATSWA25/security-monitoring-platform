"""Tests for persisted detection rule configuration."""

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.detection_rule_config import DetectionRuleConfig
from app.services.detection_rule_config_service import (
    get_detection_rule_config_by_name,
    get_detection_rule_configs,
    is_detection_rule_enabled,
    set_detection_rule_enabled,
)


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

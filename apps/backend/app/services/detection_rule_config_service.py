"""Service layer for detection rule configuration."""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.detection_rule_config import DetectionRuleConfig


async def get_detection_rule_configs(
    db: AsyncSession,
) -> list[DetectionRuleConfig]:
    """Return all persisted detection rule configurations."""

    result = await db.execute(
        select(DetectionRuleConfig).order_by(
            DetectionRuleConfig.id,
        )
    )

    return list(result.scalars().all())


async def get_detection_rule_config_by_name(
    db: AsyncSession,
    rule_name: str,
) -> DetectionRuleConfig | None:
    """Return configuration for one registered detection rule."""

    result = await db.execute(
        select(DetectionRuleConfig).where(
            DetectionRuleConfig.rule_name == rule_name,
        )
    )

    return result.scalar_one_or_none()


async def set_detection_rule_enabled(
    db: AsyncSession,
    config: DetectionRuleConfig,
    *,
    is_enabled: bool,
) -> DetectionRuleConfig:
    """
    Change whether a detection rule is operationally enabled.

    Transaction ownership remains with the calling workflow so configuration
    changes can be committed atomically with their audit records.
    """

    config.is_enabled = is_enabled

    await db.flush()
    await db.refresh(config)

    return config


async def is_detection_rule_enabled(
    db: AsyncSession,
    rule_name: str,
) -> bool:
    """
    Return whether a detection rule is enabled.

    Missing configuration currently defaults to enabled so existing Python
    rules continue operating until their persisted configuration is seeded.
    """

    config = await get_detection_rule_config_by_name(
        db=db,
        rule_name=rule_name,
    )

    if config is None:
        return True

    return config.is_enabled

"""Administrative endpoints for managing detection rule configuration."""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.permissions import require_role
from app.db.session import get_db
from app.models.user import User, UserRole
from app.schemas.detection_rule_config import (
    DetectionRuleConfigResponse,
    DetectionRuleConfigUpdate,
)
from app.services.audit_service import log_event
from app.services.detection_rule_config_service import (
    get_detection_rule_config_by_name,
    get_detection_rule_configs,
    update_detection_rule_config,
)


router = APIRouter(
    prefix="/detection-rules",
    tags=["Detection Rules"],
)


@router.get(
    "",
    response_model=list[DetectionRuleConfigResponse],
)
async def list_detection_rules(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(
        require_role(UserRole.ADMIN),
    ),
):
    """List persisted detection rule configurations."""

    return await get_detection_rule_configs(db)


@router.patch(
    "/{rule_name}",
    response_model=DetectionRuleConfigResponse,
)
async def update_detection_rule(
    rule_name: str,
    payload: DetectionRuleConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(
        require_role(UserRole.ADMIN),
    ),
):
    """Update operational configuration for a registered detection rule."""

    config = await get_detection_rule_config_by_name(
        db=db,
        rule_name=rule_name,
    )

    if config is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Detection rule not found",
        )

    previous_enabled_state = config.is_enabled
    previous_parameters = dict(config.parameters)

    try:
        config = await update_detection_rule_config(
            db=db,
            config=config,
            is_enabled=payload.is_enabled,
            parameters=payload.parameters,
        )

        await log_event(
            db=db,
            action="DETECTION_RULE_CONFIGURATION_UPDATED",
            resource="DETECTION_RULE",
            user_id=current_user.id,
            details=(
                f"Changed detection rule '{config.rule_name}' "
                f"enabled state from {previous_enabled_state} "
                f"to {config.is_enabled}; "
                f"parameters from {previous_parameters} "
                f"to {config.parameters}"
            ),
        )

        # Configuration change and audit record become permanent together.
        await db.commit()
        await db.refresh(config)

    except ValidationError as exc:
        await db.rollback()

        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=exc.errors(
                include_url=False,
                include_context=False,
            ),
        ) from exc

    except Exception:
        await db.rollback()
        raise

    return config
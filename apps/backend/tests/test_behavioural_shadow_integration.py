
"""Regression tests for optional behavioural RF shadow inference."""

from unittest.mock import patch

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.alert import Alert
from app.services.behavioural_detection.inference import (
    BehaviouralDetectionResult,
)
from app.services.login_attempt_service import record_login_attempt



async def test_real_rf_model_runs_in_shadow_mode(
    db_session: AsyncSession,
    monkeypatch,
) -> None:
    """Verify that real RF inference succeeds during authentication."""

    from app.services.behavioural_detection.inference import (
        detect_behavioural_anomaly,
    )

    monkeypatch.setattr(
        settings,
        "BEHAVIOURAL_RF_SHADOW_ENABLED",
        True,
    )

    # Capture the actual result while executing the real model.
    actual_results = []

    def capture_prediction(features):
        result = detect_behavioural_anomaly(features)
        actual_results.append(result)
        return result

    with patch(
        "app.services.behavioural_detection."
        "async_inference.detect_behavioural_anomaly",
        side_effect=capture_prediction,
    ) as prediction:
        attempt = await record_login_attempt(
            db_session,
            email="real-rf-shadow@example.com",
            successful=False,
            ip_address="192.0.2.200",
        )

    assert attempt.id is not None
    prediction.assert_called_once()

    # Assert the real prediction result, not the mock's return_value.
    assert len(actual_results) == 1

    result = actual_results[0]

    assert result.available is True
    assert result.score is not None
    assert 0.0 <= result.score <= 1.0
    assert result.model_version == "behavioural_random_forest_v3"

    # Shadow inference must not create production RF alerts.
    alerts = await db_session.execute(
        select(Alert).where(
            Alert.alert_type == "BEHAVIOURAL_RF_ANOMALY"
        )
    )

    assert alerts.scalar_one_or_none() is None

    # Prove that real model loading and inference succeeded.
    result = prediction.return_value

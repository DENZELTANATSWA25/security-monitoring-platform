"""Tests for anomaly-model construction and training."""

from datetime import datetime, timedelta

import pytest

from app.models.security_event import EventSeverity, SecurityEvent
from app.services.anomaly_detection.model import (
    AnomalyModelConfig,
    build_isolation_forest,
)
from app.services.anomaly_detection.trainer import (
    MINIMUM_TRAINING_EVENTS,
    train_anomaly_model,
)


def make_training_events(
    count: int,
) -> list[SecurityEvent]:
    """Create deterministic security events for model-training tests."""

    start = datetime(2026, 10, 1, 9, 0)

    return [
        SecurityEvent(
            event_type="SYSTEM_EVENT",
            severity=EventSeverity.INFO,
            source="server-01",
            message="Normal system heartbeat",
            user_id=None,
            telemetry_source_id=1,
            event_metadata={"environment": "test"},
            occurred_at=start + timedelta(minutes=index),
            created_at=start + timedelta(minutes=index),
        )
        for index in range(count)
    ]


def test_build_isolation_forest_uses_configuration() -> None:
    """Model construction should preserve explicit configuration."""

    config = AnomalyModelConfig(
        contamination=0.10,
        n_estimators=50,
        random_state=7,
    )

    model = build_isolation_forest(config)

    assert model.contamination == 0.10
    assert model.n_estimators == 50
    assert model.random_state == 7


def test_training_requires_minimum_number_of_events() -> None:
    """Tiny datasets should not be accepted for model training."""

    events = make_training_events(
        MINIMUM_TRAINING_EVENTS - 1
    )

    with pytest.raises(
        ValueError,
        match="events are required",
    ):
        train_anomaly_model(events)


def test_train_anomaly_model_returns_fitted_model() -> None:
    """Training should return an Isolation Forest capable of inference."""

    events = make_training_events(
        MINIMUM_TRAINING_EVENTS
    )

    model = train_anomaly_model(events)

    vector = [
        [
            0.0,
            9.0,
            3.0,
            0.0,
            1.0,
            1.0,
            23.0,
        ]
    ]

    prediction = model.predict(vector)

    assert prediction.shape == (1,)
    assert prediction[0] in (-1, 1)
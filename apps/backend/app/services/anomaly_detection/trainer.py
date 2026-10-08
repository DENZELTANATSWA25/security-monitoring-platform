"""Training logic for the anomaly-detection model."""

from collections.abc import Sequence

from sklearn.ensemble import IsolationForest

from app.models.security_event import SecurityEvent
from app.services.anomaly_detection.features import extract_event_features
from app.services.anomaly_detection.model import (
    AnomalyModelConfig,
    build_isolation_forest,
)


MINIMUM_TRAINING_EVENTS = 20

def train_anomaly_model(
    events: Sequence[SecurityEvent],
    *,
    config: AnomalyModelConfig | None = None,
) -> IsolationForest:
    """Train an Isolation Forest using historidal security events."""

    if len(events) < MINIMUM_TRAINING_EVENTS:
        raise ValueError(
            f"At least {MINIMUM_TRAINING_EVENTS} events are required "
            f"to train an anomaly model."
        )

    model_config = config or AnomalyModelConfig()

    training_data = [
        extract_event_features(event).as_vector()
        for event in events
    ]

    model = build_isolation_forest(model_config)
    model.fit(training_data)

    return model

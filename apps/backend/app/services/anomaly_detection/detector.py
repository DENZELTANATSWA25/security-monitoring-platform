"""Live inference for security-event anomaly detection."""

from pathlib import Path

from app.models.security_event import SecurityEvent
from app.services.anomaly_detection.features import extract_event_features
from app.services.anomaly_detection.model_store import load_anomaly_model
from app.services.anomaly_detection.result import AnomalyResult

def detect_anomaly(
    event: SecurityEvent,
    *,
    model_directory: Path,
) -> AnomalyResult:
    """Evaluate a security event using the persisted anomaly model."""

    try:
        stored_model = load_anomaly_model(
            directory=model_directory,
        )

        if stored_model is None:
            return AnomalyResult.unavailable(
                reason="No trained anomaly model is available.",
            )

        features = extract_event_features(event)
        vector = [features.as_vector()]

        prediction = stored_model.model.predict(vector)[0]

        decision_store = float(
            stored_model.model.decision_function(vector)[0]
        )

        if prediction == -1:
            return AnomalyResult.anomalous(
                score=decision_store,
                model_version=stored_model.version,
                reason=(
                    "Event behaviour differs from the model's ",
                    "learned baseline."
                ),
            )

        return AnomalyResult.normal(
            score=decision_store,
            model_version=stored_model.version,
        )

    except Exception:
        return AnomalyResult.unavailable(
            reason="Anomaly detection could not be completed.",
        )
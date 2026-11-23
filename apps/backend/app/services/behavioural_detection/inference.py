
"""Inference using the frozen behavioural Random Forest v3."""

from functools import lru_cache
from dataclasses import dataclass
from math import isfinite
from pathlib import Path

from app.services.behavioural_detection.features import (
    BehaviourVectorV2,
    FEATURE_NAMES,
)
from app.services.behavioural_detection.model_store import (
    DEFAULT_MODEL_PATH,
    MODEL_NAME,
    StoredBehaviouralModel,
    load_behavioural_model,
)



@dataclass(frozen=True)
class BehaviouralDetectionResult:
    """Explicit outcome of behavioural anomaly inference."""

    available: bool
    is_anomaly: bool
    score: float | None
    model_version: str | None
    reason: str | None = None


def predict_behavioural_anomaly(
    features: BehaviourVectorV2,
    *,
    stored_model: StoredBehaviouralModel,
) -> BehaviouralDetectionResult:
    """Predict malicious activity using the frozen decision threshold."""

    try:
        # Preserve the exact feature ordering used during training.
        values = list(features.as_vector())

        if len(values) != len(FEATURE_NAMES):
            raise ValueError("Unexpected feature vector length.")

        if not all(
            isinstance(value, (int, float)) and isfinite(value)
            for value in values
        ):
            raise ValueError("Feature vector contains invalid values.")

        if stored_model.feature_names != tuple(FEATURE_NAMES):
            raise ValueError("Model feature ordering mismatch.")

        # Class 1 represents malicious activity.
        classes = list(stored_model.model.classes_)
        if classes != [0, 1]:
            raise ValueError("Unexpected classifier labels.")

        probabilities = stored_model.model.predict_proba([values])

        if probabilities.shape != (1, 2):
            raise ValueError("Unexpected probability output shape.")

        score = float(probabilities[0, classes.index(1)])

        if not isfinite(score) or not 0.0 <= score <= 1.0:
            raise ValueError("Invalid predicted probability.")

        return BehaviouralDetectionResult(
            available=True,
            is_anomaly=score >= stored_model.threshold,
            score=score,
            model_version=stored_model.name,
        )

    except Exception:
        # Prediction errors must not be interpreted as benign events.
        return BehaviouralDetectionResult(
            available=False,
            is_anomaly=False,
            score=None,
            model_version=MODEL_NAME,
            reason="Behavioural prediction unavailable.",
        )

@lru_cache(maxsize=1)
def get_cached_behavioural_model(
    path: Path,
) -> StoredBehaviouralModel:
    """Load the verified model once per application process."""
    return load_behavioural_model(path)

def detect_behavioural_anomaly(
    features: BehaviourVectorV2,
    *,
    model_path: Path = DEFAULT_MODEL_PATH,
) -> BehaviouralDetectionResult:
    """Load the approved model and run one behavioural prediction."""

    try:
        stored_model = get_cached_behavioural_model(Path(model_path))
    except Exception:
        return BehaviouralDetectionResult(
            available=False,
            is_anomaly=False,
            score=None,
            model_version=MODEL_NAME,
            reason="Behavioural model unavailable.",
        )

    return predict_behavioural_anomaly(
        features,
        stored_model=stored_model,
    )

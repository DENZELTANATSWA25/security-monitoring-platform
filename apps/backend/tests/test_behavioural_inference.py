
"""Tests for frozen behavioural Random Forest inference."""

from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import Mock

import numpy as np
import pytest

from app.services.behavioural_detection.features import (
    BehaviourEventV2,
    BehaviourFeatureExtractorV2,
    FEATURE_NAMES,
)
from app.services.behavioural_detection.inference import (
    detect_behavioural_anomaly,
    predict_behavioural_anomaly,
)
from app.services.behavioural_detection.model_store import (
    MODEL_NAME,
    MODEL_THRESHOLD,
    StoredBehaviouralModel,
    load_behavioural_model,
)


def make_features():
    """Produce a valid, deterministic 22-feature vector."""

    event = BehaviourEventV2(
        timestamp=datetime(2026, 11, 20, tzinfo=timezone.utc),
        source="platform_authentication",
        event_type="authentication",
        user_id="test@example.com",
        authentication_success=False,
        ip_address="192.0.2.1",
        device_id=None,
    )

    return BehaviourFeatureExtractorV2().transform_one(event)


def make_stored_model(probability: float):
    """Create a controlled classifier for threshold tests."""

    classifier = Mock()
    classifier.classes_ = np.array([0, 1])
    classifier.predict_proba.return_value = np.array(
        [[1.0 - probability, probability]]
    )

    stored = StoredBehaviouralModel(
        model=classifier,
        threshold=MODEL_THRESHOLD,
        name=MODEL_NAME,
        feature_schema="behavioural-v2",
        feature_names=tuple(FEATURE_NAMES),
    )

    return stored, classifier


def test_probability_below_threshold_is_not_anomalous() -> None:
    stored, classifier = make_stored_model(0.20)

    result = predict_behavioural_anomaly(
        make_features(),
        stored_model=stored,
    )

    assert result.available is True
    assert result.is_anomaly is False
    assert result.score == pytest.approx(0.20)
    classifier.predict_proba.assert_called_once()


def test_probability_above_threshold_is_anomalous() -> None:
    stored, _ = make_stored_model(0.90)

    result = predict_behavioural_anomaly(
        make_features(),
        stored_model=stored,
    )

    assert result.available is True
    assert result.is_anomaly is True
    assert result.score == pytest.approx(0.90)


def test_probability_equal_to_threshold_triggers() -> None:
    stored, _ = make_stored_model(MODEL_THRESHOLD)

    result = predict_behavioural_anomaly(
        make_features(),
        stored_model=stored,
    )

    assert result.available is True
    assert result.is_anomaly is True


@pytest.mark.parametrize(
    "probability",
    [float("nan"), float("inf"), -0.1, 1.1],
)
def test_invalid_probabilities_are_unavailable(
    probability: float,
) -> None:
    stored, _ = make_stored_model(probability)

    result = predict_behavioural_anomaly(
        make_features(),
        stored_model=stored,
    )

    assert result.available is False
    assert result.is_anomaly is False
    assert result.score is None


def test_prediction_exception_is_unavailable() -> None:
    stored, classifier = make_stored_model(0.5)
    classifier.predict_proba.side_effect = RuntimeError(
        "Prediction failed"
    )

    result = predict_behavioural_anomaly(
        make_features(),
        stored_model=stored,
    )

    assert result.available is False
    assert result.score is None


def test_feature_order_mismatch_is_rejected() -> None:
    stored, classifier = make_stored_model(0.9)

    invalid_stored = StoredBehaviouralModel(
        model=classifier,
        threshold=stored.threshold,
        name=stored.name,
        feature_schema=stored.feature_schema,
        feature_names=tuple(reversed(FEATURE_NAMES)),
    )

    result = predict_behavioural_anomaly(
        make_features(),
        stored_model=invalid_stored,
    )

    assert result.available is False
    classifier.predict_proba.assert_not_called()


def test_missing_artifact_returns_unavailable(
    tmp_path: Path,
) -> None:
    result = detect_behavioural_anomaly(
        make_features(),
        model_path=tmp_path / "missing.joblib",
    )

    assert result.available is False
    assert result.is_anomaly is False
    assert result.score is None


def test_real_frozen_model_predicts_valid_probability() -> None:
    """Smoke-test actual inference against the verified artifact."""

    stored = load_behavioural_model()

    result = predict_behavioural_anomaly(
        make_features(),
        stored_model=stored,
    )

    assert result.available is True
    assert result.model_version == MODEL_NAME
    assert result.score is not None
    assert 0.0 <= result.score <= 1.0

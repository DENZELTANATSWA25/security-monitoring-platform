
"""Regression tests for single-threaded behavioural RF inference."""

from hashlib import sha256

import pytest

from app.services.behavioural_detection.features import (
    FEATURE_NAMES,
)
from app.services.behavioural_detection.inference import (
    get_cached_behavioural_model,
    predict_behavioural_anomaly,
)
from app.services.behavioural_detection.model_store import (
    DEFAULT_MODEL_PATH,
    MODEL_SHA256,
    MODEL_THRESHOLD,
    load_behavioural_model,
)

from tests.test_behavioural_inference import make_features


@pytest.fixture(autouse=True)
def clear_model_cache():
    """Keep cache state independent between tests."""

    get_cached_behavioural_model.cache_clear()
    yield
    get_cached_behavioural_model.cache_clear()


def test_runtime_model_uses_single_thread():
    """Inference uses one worker without changing model structure."""

    stored = get_cached_behavioural_model(DEFAULT_MODEL_PATH)

    assert stored.model.n_jobs == 1
    assert stored.model.n_estimators == 300
    assert stored.model.n_features_in_ == 22
    assert stored.threshold == MODEL_THRESHOLD
    assert stored.feature_names == tuple(FEATURE_NAMES)


def test_original_artifact_retains_parallel_configuration():
    """The verified model file must remain unchanged."""

    original = load_behavioural_model(DEFAULT_MODEL_PATH)
    runtime = get_cached_behavioural_model(DEFAULT_MODEL_PATH)

    assert original.model.n_jobs == -1
    assert runtime.model.n_jobs == 1
    assert original.model is not runtime.model

    # Recheck the original file bytes.
    digest = sha256(DEFAULT_MODEL_PATH.read_bytes()).hexdigest()
    assert digest == MODEL_SHA256


def test_runtime_prediction_matches_original():
    """Changing execution parallelism must preserve predictions."""

    features = make_features()

    original = load_behavioural_model(DEFAULT_MODEL_PATH)
    runtime = get_cached_behavioural_model(DEFAULT_MODEL_PATH)

    original_result = predict_behavioural_anomaly(
        features,
        stored_model=original,
    )

    runtime_result = predict_behavioural_anomaly(
        features,
        stored_model=runtime,
    )

    assert original_result.available is True
    assert runtime_result.available is True

    assert runtime_result.score == pytest.approx(
        original_result.score,
        abs=1e-12,
    )

    assert runtime_result.is_anomaly == original_result.is_anomaly


def test_cached_model_is_reused():
    """Repeated inference must not reload or reconfigure the model."""

    first = get_cached_behavioural_model(DEFAULT_MODEL_PATH)
    second = get_cached_behavioural_model(DEFAULT_MODEL_PATH)

    assert first is second
    assert second.model.n_jobs == 1

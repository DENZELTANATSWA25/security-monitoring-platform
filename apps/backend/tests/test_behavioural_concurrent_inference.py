
"""Concurrency regression tests for frozen behavioural RF inference."""

from concurrent.futures import ThreadPoolExecutor

import pytest

from app.services.behavioural_detection.inference import (
    get_cached_behavioural_model,
    predict_behavioural_anomaly,
)
from app.services.behavioural_detection.model_store import (
    DEFAULT_MODEL_PATH,
)

from tests.test_behavioural_inference import make_features


@pytest.fixture(autouse=True)
def clear_model_cache():
    """Ensure each test starts with a fresh cached model."""
    get_cached_behavioural_model.cache_clear()
    yield
    get_cached_behavioural_model.cache_clear()


@pytest.mark.parametrize("workers", [1, 5, 10, 20])
def test_concurrent_predictions_are_consistent(workers: int) -> None:
    """Shared-model predictions must agree under concurrent access."""

    stored = get_cached_behavioural_model(DEFAULT_MODEL_PATH)
    features = make_features()

    # Establish a deterministic reference prediction.
    reference = predict_behavioural_anomaly(
        features,
        stored_model=stored,
    )

    assert reference.available is True
    assert reference.score is not None
    assert stored.model.n_jobs == 1

    def predict():
        """Use the same cached classifier without changing its state."""
        return predict_behavioural_anomaly(
            features,
            stored_model=stored,
        )

    # Run 40 predictions using independent worker threads.
    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = list(executor.map(lambda _: predict(), range(40)))

    assert len(results) == 40

    for result in results:
        assert result.available is True
        assert result.score == pytest.approx(
            reference.score,
            abs=1e-12,
        )
        assert result.is_anomaly == reference.is_anomaly
        assert result.model_version == reference.model_version

    # Concurrency must not change the runtime execution configuration.
    assert stored.model.n_jobs == 1


"""Tests for caching the verified behavioural model."""

from pathlib import Path
from unittest.mock import patch

from app.services.behavioural_detection.inference import (
    detect_behavioural_anomaly,
    get_cached_behavioural_model,
)
from app.services.behavioural_detection.model_store import (
    DEFAULT_MODEL_PATH,
)

from app.services.behavioural_detection.features import (
    BehaviourEventV2,
    BehaviourFeatureExtractorV2,
)

from datetime import datetime, timezone


def make_features():
    """Create a valid vector for cache regression tests."""

    event = BehaviourEventV2(
        timestamp=datetime(2026, 11, 20, tzinfo=timezone.utc),
        source="platform_authentication",
        event_type="authentication",
        user_id="cache@example.com",
        authentication_success=False,
        ip_address="192.0.2.1",
        device_id=None,
    )

    return BehaviourFeatureExtractorV2().transform_one(event)


def test_model_is_loaded_once_for_repeated_predictions() -> None:
    """Repeated predictions should reuse the same verified model."""

    get_cached_behavioural_model.cache_clear()

    with patch(
        "app.services.behavioural_detection.inference."
        "load_behavioural_model",
        wraps=__import__(
            "app.services.behavioural_detection.model_store",
            fromlist=["load_behavioural_model"],
        ).load_behavioural_model,
    ) as loader:
        first = detect_behavioural_anomaly(make_features())
        second = detect_behavioural_anomaly(make_features())

    assert first.available is True
    assert second.available is True
    assert loader.call_count == 1

    get_cached_behavioural_model.cache_clear()


def test_cache_can_be_cleared() -> None:
    """Cache invalidation must allow a fresh verified load."""

    get_cached_behavioural_model.cache_clear()

    first = get_cached_behavioural_model(
        Path(DEFAULT_MODEL_PATH)
    )

    get_cached_behavioural_model.cache_clear()

    second = get_cached_behavioural_model(
        Path(DEFAULT_MODEL_PATH)
    )

    assert first is not second

    get_cached_behavioural_model.cache_clear()

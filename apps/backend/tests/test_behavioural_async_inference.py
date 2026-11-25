"""Tests for asynchronous behavioural inference strategies."""

import pytest

from app.services.behavioural_detection.async_inference import (
    run_behavioural_inference,
)
from tests.test_behavioural_inference import make_features


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "strategy",
    ["direct", "threaded", "bounded"],
)
async def test_strategies_produce_equivalent_predictions(strategy):
    """Execution strategy must not change model predictions."""
    features = make_features()

    baseline = await run_behavioural_inference(
        features,
        strategy="direct",
    )

    candidate = await run_behavioural_inference(
        features,
        strategy=strategy,
    )

    assert baseline.available
    assert candidate.available
    assert candidate.model_version == baseline.model_version
    assert candidate.is_anomaly == baseline.is_anomaly
    assert candidate == baseline


@pytest.mark.asyncio
async def test_invalid_strategy_is_rejected():
    """Reject unsupported execution strategies."""
    with pytest.raises(ValueError):
        await run_behavioural_inference(
            make_features(),
            strategy="invalid",
        )

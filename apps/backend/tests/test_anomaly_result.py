"""Tests for anomaly-detection result types."""

from app.services.anomaly_detection.result import AnomalyResult


def test_unavailable_result() -> None:
    """Unavailable detection should not classify an event as anomalous."""

    result = AnomalyResult.unavailable(
        reason="No trained model is available.",
    )

    assert result.available is False
    assert result.is_anomaly is False
    assert result.score is None
    assert result.model_version is None
    assert result.reason == "No trained model is available."


def test_normal_result() -> None:
    """A successful normal prediction should preserve model metadata."""

    result = AnomalyResult.normal(
        score=0.42,
        model_version="v1",
    )

    assert result.available is True
    assert result.is_anomaly is False
    assert result.score == 0.42
    assert result.model_version == "v1"
    assert result.reason is None


def test_anomalous_result() -> None:
    """An anomalous prediction should contain explainable metadata."""

    result = AnomalyResult.anomalous(
        score=0.91,
        model_version="v1",
        reason="Event differs significantly from learned behaviour.",
    )

    assert result.available is True
    assert result.is_anomaly is True
    assert result.score == 0.91
    assert result.model_version == "v1"
    assert result.reason == (
        "Event differs significantly from learned behaviour."
    )
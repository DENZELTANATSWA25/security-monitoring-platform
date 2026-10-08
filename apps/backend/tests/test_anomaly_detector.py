"""Tests for live anomaly-model inference."""

from pathlib import Path

from app.models.security_event import SecurityEvent
from app.services.anomaly_detection.detector import detect_anomaly
from app.services.anomaly_detection.model_store import save_anomaly_model
from app.services.anomaly_detection.trainer import (
    MINIMUM_TRAINING_EVENTS,
    train_anomaly_model,
)
from tests.test_anomaly_training import make_training_events


def test_detector_returns_unavailable_without_model(
    tmp_path: Path,
) -> None:
    """Missing model artifacts should not crash inference."""

    event = make_training_events(1)[0]

    result = detect_anomaly(
        event,
        model_directory=tmp_path,
    )

    assert result.available is False
    assert result.is_anomaly is False
    assert result.score is None
    assert result.model_version is None


def test_detector_runs_inference_with_saved_model(
    tmp_path: Path,
) -> None:
    """A persisted model should support live event inference."""

    events = make_training_events(
        MINIMUM_TRAINING_EVENTS
    )
    model = train_anomaly_model(events)

    save_anomaly_model(
        model,
        directory=tmp_path,
        version="v1",
    )

    result = detect_anomaly(
        events[0],
        model_directory=tmp_path,
    )

    assert result.available is True
    assert isinstance(result.is_anomaly, bool)
    assert isinstance(result.score, float)
    assert result.model_version == "v1"


def test_detector_fails_open_for_corrupt_model(
    tmp_path: Path,
) -> None:
    """Corrupt model artifacts should produce an unavailable result."""

    model_path = tmp_path / "model.joblib"
    metadata_path = tmp_path / "metadata.joblib"

    model_path.write_text(
        "this is not a valid model",
    )
    metadata_path.write_text(
        "this is not valid metadata",
    )

    event: SecurityEvent = make_training_events(1)[0]

    result = detect_anomaly(
        event,
        model_directory=tmp_path,
    )

    assert result.available is False
    assert result.is_anomaly is False
    assert result.score is None
    assert result.model_version is None
    assert result.reason == (
        "Anomaly detection could not be completed."
    )
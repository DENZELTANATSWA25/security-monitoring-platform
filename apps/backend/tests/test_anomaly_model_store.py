"""Tests for anomaly-model persistence."""

from pathlib import Path

from app.services.anomaly_detection.model_store import (
    load_anomaly_model,
    save_anomaly_model,
)
from app.services.anomaly_detection.trainer import (
    MINIMUM_TRAINING_EVENTS,
    train_anomaly_model,
)
from tests.test_anomaly_training import make_training_events


def test_save_and_load_anomaly_model(
    tmp_path: Path,
) -> None:
    """A trained model should survive a save/load cycle."""

    events = make_training_events(
        MINIMUM_TRAINING_EVENTS
    )
    model = train_anomaly_model(events)

    save_anomaly_model(
        model,
        directory=tmp_path,
        version="v1",
    )

    stored = load_anomaly_model(
        directory=tmp_path,
    )

    assert stored is not None
    assert stored.version == "v1"

    vector = [
        [
            0.0,
            9.0,
            3.0,
            0.0,
            1.0,
            1.0,
            23.0,
        ]
    ]

    original_prediction = model.predict(vector)
    loaded_prediction = stored.model.predict(vector)

    assert (
        original_prediction.tolist()
        == loaded_prediction.tolist()
    )


def test_load_returns_none_when_model_is_missing(
    tmp_path: Path,
) -> None:
    """An absent model should be represented without crashing."""

    stored = load_anomaly_model(
        directory=tmp_path,
    )

    assert stored is None


def test_save_rejects_empty_version(
    tmp_path: Path,
) -> None:
    """Every persisted model must have a meaningful version."""

    events = make_training_events(
        MINIMUM_TRAINING_EVENTS
    )
    model = train_anomaly_model(events)

    try:
        save_anomaly_model(
            model,
            directory=tmp_path,
            version="   ",
        )
    except ValueError as exc:
        assert str(exc) == "Model version must not be empty."
    else:
        raise AssertionError(
            "Expected empty model version to be rejected."
        )
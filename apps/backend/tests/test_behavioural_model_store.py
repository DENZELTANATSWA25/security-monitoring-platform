
"""Tests for loading the frozen behavioural RF v3 artifact."""

from pathlib import Path
from unittest.mock import patch

import pytest

from app.services.behavioural_detection.features import FEATURE_NAMES
from app.services.behavioural_detection.model_store import (
    BehaviouralModelError,
    MODEL_NAME,
    MODEL_SHA256,
    MODEL_THRESHOLD,
    load_behavioural_model,
)


MODEL_PATH = Path("models/behavioural_rf_v3/model.joblib")


def test_frozen_model_loads_successfully() -> None:
    stored = load_behavioural_model(MODEL_PATH)

    assert stored.name == MODEL_NAME
    assert stored.threshold == MODEL_THRESHOLD
    assert stored.feature_schema == "behavioural-v2"
    assert stored.feature_names == tuple(FEATURE_NAMES)
    assert stored.model.n_features_in_ == 22
    assert list(stored.model.classes_) == [0, 1]


def test_missing_model_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(
        BehaviouralModelError,
        match="could not be loaded",
    ):
        load_behavioural_model(tmp_path / "missing.joblib")


def test_modified_model_is_rejected_before_deserialisation(
    tmp_path: Path,
) -> None:
    corrupted = tmp_path / "model.joblib"
    corrupted.write_bytes(MODEL_PATH.read_bytes() + b"modified")

    with patch(
        "app.services.behavioural_detection.model_store.joblib.load"
    ) as mocked_load:
        with pytest.raises(
            BehaviouralModelError,
            match="SHA-256 mismatch",
        ):
            load_behavioural_model(corrupted)

        mocked_load.assert_not_called()


def test_invalid_file_is_rejected_before_deserialisation(
    tmp_path: Path,
) -> None:
    invalid = tmp_path / "model.joblib"
    invalid.write_bytes(b"not a trusted model")

    with patch(
        "app.services.behavioural_detection.model_store.joblib.load"
    ) as mocked_load:
        with pytest.raises(
            BehaviouralModelError,
            match="SHA-256 mismatch",
        ):
            load_behavioural_model(invalid)

        mocked_load.assert_not_called()


def test_expected_hash_is_frozen() -> None:
    assert MODEL_SHA256 == (
        "a73683e95d48cfe8d98fbc24dd58baca5063ce46b7d23dbf898c54081ce8a53f"
    )

"""Tests for stable behavioural model provisioning paths."""

from pathlib import Path

from app.services.behavioural_detection.model_store import (
    DEFAULT_MODEL_PATH,
    MODEL_SHA256,
    load_behavioural_model,
)

from hashlib import sha256


def test_model_path_is_absolute() -> None:
    """Model location must not depend on the process working directory."""

    assert DEFAULT_MODEL_PATH.is_absolute()
    assert DEFAULT_MODEL_PATH.name == "model.joblib"


def test_model_loading_is_independent_of_cwd(
    tmp_path: Path,
    monkeypatch,
) -> None:
    """Changing directories must not break verified model loading."""

    monkeypatch.chdir(tmp_path)

    stored_model = load_behavioural_model()

    assert stored_model.name == "behavioural_random_forest_v3"
    assert len(stored_model.feature_names) == 22


def test_provisioned_model_checksum() -> None:
    """The provisioned artifact must match the approved frozen checksum."""

    digest = sha256(DEFAULT_MODEL_PATH.read_bytes()).hexdigest()

    assert digest == MODEL_SHA256
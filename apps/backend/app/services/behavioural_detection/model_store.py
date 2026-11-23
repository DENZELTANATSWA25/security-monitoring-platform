
"""Validated loader for the frozen behavioural Random Forest v3."""

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestClassifier

from app.services.behavioural_detection.features import (
    FEATURE_NAMES,
    FEATURE_SCHEMA_VERSION,
)


MODEL_SHA256 = (
    "a73683e95d48cfe8d98fbc24dd58baca5063ce46b7d23dbf898c54081ce8a53f"
)
MODEL_NAME = "behavioural_random_forest_v3"
MODEL_THRESHOLD = 0.6244841045172164
MODEL_RANDOM_STATE = 42

DEFAULT_MODEL_PATH = Path(
    "models/behavioural_rf_v3/model.joblib"
)


class BehaviouralModelError(RuntimeError):
    """The frozen behavioural model is missing or invalid."""


@dataclass(frozen=True)
class StoredBehaviouralModel:
    """A validated model and its frozen inference configuration."""

    model: RandomForestClassifier
    threshold: float
    name: str
    feature_schema: str
    feature_names: tuple[str, ...]


def load_behavioural_model(
    path: Path = DEFAULT_MODEL_PATH,
) -> StoredBehaviouralModel:
    """Load only the approved, schema-compatible RF v3 artifact."""

    path = Path(path)

    try:
        # Verify bytes before invoking joblib's pickle deserialisation.
        with path.open("rb") as artifact_file:
            digest = sha256()

            for chunk in iter(
                lambda: artifact_file.read(1024 * 1024),
                b"",
            ):
                digest.update(chunk)

        if digest.hexdigest() != MODEL_SHA256:
            raise BehaviouralModelError(
                "Behavioural model SHA-256 mismatch."
            )

        artifact = joblib.load(path)

        if not isinstance(artifact, dict):
            raise BehaviouralModelError(
                "Behavioural artifact must be a dictionary."
            )

        required_keys = {
            "model",
            "threshold",
            "feature_schema",
            "feature_names",
            "model_name",
            "random_state",
            "threshold_selection",
        }

        if not required_keys.issubset(artifact):
            raise BehaviouralModelError(
                "Behavioural artifact metadata is incomplete."
            )

        model = artifact["model"]

        if type(model) is not RandomForestClassifier:
            raise BehaviouralModelError(
                "Unexpected behavioural model type."
            )

        if artifact["model_name"] != MODEL_NAME:
            raise BehaviouralModelError(
                "Unexpected behavioural model name."
            )

        if artifact["feature_schema"] != FEATURE_SCHEMA_VERSION:
            raise BehaviouralModelError(
                "Behavioural feature schema mismatch."
            )

        if tuple(artifact["feature_names"]) != tuple(FEATURE_NAMES):
            raise BehaviouralModelError(
                "Behavioural feature ordering mismatch."
            )

        if (
            type(artifact["threshold"]) is not float
            or artifact["threshold"] != MODEL_THRESHOLD
        ):
            raise BehaviouralModelError(
                "Frozen decision threshold mismatch."
            )

        if (
            type(artifact["random_state"]) is not int
            or artifact["random_state"] != MODEL_RANDOM_STATE
        ):
            raise BehaviouralModelError(
                "Unexpected training random state."
            )

        if model.n_features_in_ != len(FEATURE_NAMES):
            raise BehaviouralModelError(
                "Model input dimension mismatch."
            )

        # The positive class must represent malicious activity.
        if list(model.classes_) != [0, 1]:
            raise BehaviouralModelError(
                "Unexpected classifier labels."
            )

        return StoredBehaviouralModel(
            model=model,
            threshold=MODEL_THRESHOLD,
            name=MODEL_NAME,
            feature_schema=FEATURE_SCHEMA_VERSION,
            feature_names=tuple(FEATURE_NAMES),
        )

    except BehaviouralModelError:
        raise

    except Exception as exc:
        # Avoid exposing filesystem details in application-level errors.
        raise BehaviouralModelError(
            "Behavioural model could not be loaded."
        ) from exc

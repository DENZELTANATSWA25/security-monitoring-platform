"""Persistence for trained anomaly-detection models."""

from dataclasses import dataclass
from pathlib import Path

import joblib
from sklearn.ensemble import IsolationForest

MODEL_FILENAME = "model.joblib"
METADATA_FILENAME = "metadata.joblib"

@dataclass(frozen=True)
class StoredAnomalyModel:
    """A trained model loaded together with its version."""

    model: IsolationForest
    version: str

def save_anomaly_model(
    model: IsolationForest,
    *,
    directory: Path,
    version: str,
) -> None:
    """Persist a trained anomaly model and its metadata."""

    if not version.strip():
        raise ValueError("Model version must not be empty.")

    directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    joblib.dump(
        model,
        directory / MODEL_FILENAME,
    )

    joblib.dump(
        {"version": version},
        directory / METADATA_FILENAME,
    )

def load_anomaly_model(
    *,
    directory: Path,
) -> StoredAnomalyModel | None:
    """Load the persisted anomaly model, if one exists."""

    model_path = directory / MODEL_FILENAME
    metadata_path = directory / METADATA_FILENAME

    if not model_path.exists() or not metadata_path.exists():
        return None

    model = joblib.load(model_path)
    metadata = joblib.load(metadata_path)

    return StoredAnomalyModel(
        model=model,
        version=metadata["version"],
    )
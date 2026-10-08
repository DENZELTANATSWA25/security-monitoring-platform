"""Model congiguration for anomaly detection."""

from dataclasses import dataclass

from sklearn.ensemble import IsolationForest

@dataclass(frozen=True)
class AnomalyModelConfig:
    """Configuration used to build the Isolation forest models."""

    contamination: float = 0.05
    n_estimators: int = 100
    random_state: int = 42

def build_isolation_forest(
        config: AnomalyModelConfig,
) -> IsolationForest:
    """Build an untrained Isolation Forest from application configuration."""

    return IsolationForest(
        n_estimators=config.n_estimators,
        contamination=config.contamination,
        random_state=config.random_state,
    )
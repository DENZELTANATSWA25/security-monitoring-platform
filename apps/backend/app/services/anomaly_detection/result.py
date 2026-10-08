"""Result types for ML anomaly detection."""

from dataclasses import dataclass


@dataclass(frozen=True)
class AnomalyResult:
    """Result produced by the anomaly-detection subsystem."""

    available: bool
    is_anomaly: bool
    score: float | None = None
    model_version: str | None = None
    reason: str | None = None

    @classmethod
    def unavailable(
        cls,
        *,
        reason: str,
    ) -> "AnomalyResult":
        """Return a result when anomaly detection cannot run."""

        return cls(
            available=False,
            is_anomaly=False,
            score=None,
            model_version=None,
            reason=reason,
        )

    @classmethod
    def normal(
        cls,
        *,
        score: float,
        model_version: str,
    ) -> "AnomalyResult":
        """Return a result for an event considered normal."""

        return cls(
            available=True,
            is_anomaly=False,
            score=score,
            model_version=model_version,
            reason=None,
        )

    @classmethod
    def anomalous(
        cls,
        *,
        score: float,
        model_version: str,
        reason: str,
    ) -> "AnomalyResult":
        """Return a result for an anomalous event."""

        return cls(
            available=True,
            is_anomaly=True,
            score=score,
            model_version=model_version,
            reason=reason,
        )
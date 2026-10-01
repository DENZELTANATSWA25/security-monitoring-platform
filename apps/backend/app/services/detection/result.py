# Shared result type returned by detection rules.

from dataclasses import dataclass

@dataclass(frozen=True)
class DetectionResult:
    """
    Result produced by a detection rule.

    A non-triggered result contains only the triggered flag.
    Triggered results contain the information required to create an alert.
    """

    triggered: bool
    alert_type: str | None = None
    severity: str | None = None
    message: str | None = None

    @classmethod
    def not_triggered(cls) -> "DetectionResult":
        # Return a standard result for a rule that did not trigger.
        return cls(triggered=False)

    @classmethod
    def triggered_alert(
        cls,
        *,
        alert_type: str,
        severity: str,
        message: str,
    ) -> "DetectionResult":
        # Return a validated representation of a triggered rule.
        return cls(
            triggered=True,
            alert_type=alert_type,
            severity=severity,
            message=message,
        )
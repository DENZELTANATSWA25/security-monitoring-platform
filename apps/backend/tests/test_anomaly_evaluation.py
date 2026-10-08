"""Tests for anomaly-detection evaluation."""

from datetime import datetime, timedelta

import pytest

from app.models.security_event import EventSeverity, SecurityEvent
from app.services.anomaly_detection.evaluation import (
    evaluate_anomaly_model,
)
from app.services.anomaly_detection.model import AnomalyModelConfig
from app.services.anomaly_detection.trainer import train_anomaly_model

class FakeModel:
    """Model stub returning deterministic predictions."""

    def __init__(
        self,
        predictions: list[int],
    ) -> None:
        self.predictions = predictions

    def predict(
        self,
        vectors: list[list[float]],
    ) -> list[int]:
        return self.predictions


def make_evaluation_events(
    count: int,
) -> list[SecurityEvent]:
    """Create events suitable for evaluation tests."""

    return [
        SecurityEvent(
            event_type="EVALUATION_EVENT",
            severity=EventSeverity.INFO,
            source="evaluation-test",
            message=f"Evaluation event {index}",
            created_at=datetime(
                2026,
                10,
                8,
                12,
                0,
            ),
        )
        for index in range(count)
    ]


def test_evaluation_calculates_classification_metrics() -> None:
    """Evaluation should calculate TP, FP, TN, FN and derived metrics."""

    events = make_evaluation_events(4)

    # Expected labels:
    # anomaly, normal, anomaly, normal
    labels = [
        True,
        False,
        True,
        False,
    ]

    # Model predictions:
    # anomaly, anomaly, normal, normal
    #
    # Therefore:
    # TP = 1
    # FP = 1
    # FN = 1
    # TN = 1
    model = FakeModel(
        predictions=[
            -1,
            -1,
            1,
            1,
        ]
    )

    metrics = evaluate_anomaly_model(
        model,  # type: ignore[arg-type]
        events,
        labels,
    )

    assert metrics.true_positives == 1
    assert metrics.false_positives == 1
    assert metrics.true_negatives == 1
    assert metrics.false_negatives == 1

    assert metrics.precision == pytest.approx(0.5)
    assert metrics.recall == pytest.approx(0.5)
    assert metrics.f1_score == pytest.approx(0.5)


def test_evaluation_rejects_mismatched_labels() -> None:
    """Every evaluation event must have a corresponding label."""

    events = make_evaluation_events(2)

    with pytest.raises(
        ValueError,
        match="same number",
    ):
        evaluate_anomaly_model(
            FakeModel([1, 1]),  # type: ignore[arg-type]
            events,
            [False],
        )


def test_evaluation_rejects_empty_dataset() -> None:
    """An empty dataset cannot provide meaningful evaluation metrics."""

    with pytest.raises(
        ValueError,
        match="at least one event",
    ):
        evaluate_anomaly_model(
            FakeModel([]),  # type: ignore[arg-type]
            [],
            [],
        )

def test_real_model_detects_controlled_anomalous_behaviour() -> None:
    """
    A real Isolation Forest should distinguish deliberately unusual
    events from the normal behaviour used during training.
    """

    start = datetime(
        2026,
        10,
        5,
        9,
        0,
    )

    training_events = [
        SecurityEvent(
            event_type="SYSTEM_ACTIVITY",
            severity=(
                EventSeverity.WARNING
                if index % 10 == 0
                else EventSeverity.INFO
            ),
            source=F"server-{index % 3} + 1:02d",
            message=(
                f"Routine authenticated system activity "
                f"record {index}"
            ),
            user_id=(
                index % 20
                if index % 4 == 0
                else None
            ),
            telemetry_source_id=(
                (index % 3) + 1
            ),
            event_metadata={
                "environment": "production",
                **(
                    {"region": "primary"}
                    if index % 3 == 0
                    else {}
                ),
            },
            occurred_at=(
                start
                + timedelta(
                    days=index % 3,
                    minutes=(index % 96) * 5,
                )
            ),
            created_at=(
                start
                + timedelta(
                    days=index % 3,
                    minutes=(index % 96) * 5,
                )
            ),
        )
        for index in range(100)
    ]

    model = train_anomaly_model(
        training_events,
        config=AnomalyModelConfig(
            contamination=0.05,
            n_estimators=100,
            random_state=42,
        ),
    )

    normal_events = [
        SecurityEvent(
            event_type="SYSTEM_ACTIVITY",
            severity=EventSeverity.INFO,
            source="server-01",
            message=(
                "Routine authenticated system activity "
                f"record {index}"
            ),
            user_id=None,
            telemetry_source_id=1,
            event_metadata={
                "environment": "production",
            },
            occurred_at=(
                start
                + timedelta(
                    days=1,
                    minutes=10 + index * 5,
                )
            ),
            created_at=(
                start
                + timedelta(
                    days=1,
                    minutes=10 + index * 5,
                )
            ),
        )
        for index in range(10)
    ]

    anomalous_events = [
        SecurityEvent(
            event_type="UNUSUAL_SECURITY_EVENT",
            severity=EventSeverity.CRITICAL,
            source="unknown-source",
            message=(
                "Highly unusual security event containing "
                "substantially more information than normal "
                "heartbeat telemetry."
            ),
            user_id=9000 + index,
            telemetry_source_id=None,
            event_metadata={
                "field_1": "value",
                "field_2": "value",
                "field_3": "value",
                "field_4": "value",
                "field_5": "value",
            },
            occurred_at=datetime(
                2026,
                10,
                8,
                3,
                index,
            ),
            created_at=datetime(
                2026,
                10,
                8,
                3,
                index,
            ),
        )
        for index in range(10)
    ]

    evaluation_events = (
        normal_events
        + anomalous_events
    )

    labels = (
        [False] * len(normal_events)
        + [True] * len(anomalous_events)
    )

    metrics = evaluate_anomaly_model(
        model,
        evaluation_events,
        labels,
    )

    assert metrics.true_positives > 0
    assert metrics.recall > 0.0
    assert metrics.precision > 0.0
    assert metrics.f1_score > 0.0
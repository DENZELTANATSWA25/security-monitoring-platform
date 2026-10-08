"""Evaluation utilities for the anomaly-detection model."""

from dataclasses import dataclass
from collections.abc import Sequence

from sklearn.ensemble import IsolationForest

from app.models.security_event import SecurityEvent
from app.services.anomaly_detection.features import extract_event_features


@dataclass(frozen=True)
class EvaluationMetrics:
    """Classification metrics for anomaly-detection evaluation."""

    true_positives: int
    false_positives: int
    true_negatives: int
    false_negatives: int
    precision: float
    recall: float
    f1_score: float


def evaluate_anomaly_model(
    model: IsolationForest,
    events: Sequence[SecurityEvent],
    labels: Sequence[bool],
) -> EvaluationMetrics:
    """
    Evaluate a trained anomaly model against labelled security events.

    labels use True for anomaly and False for normal.
    """

    if len(events) != len(labels):
        raise ValueError(
            "Events and labels must contain the same number of items."
        )

    if not events:
        raise ValueError(
            "Evaluation requires at least one event."
        )

    vectors = [
        extract_event_features(event).as_vector()
        for event in events
    ]

    predictions = model.predict(vectors)

    predicted_anomalies = [
        prediction == -1
        for prediction in predictions
    ]

    true_positives = sum(
        predicted and actual
        for predicted, actual in zip(
            predicted_anomalies,
            labels,
        )
    )

    false_positives = sum(
        predicted and not actual
        for predicted, actual in zip(
            predicted_anomalies,
            labels,
        )
    )

    true_negatives = sum(
        not predicted and not actual
        for predicted, actual in zip(
            predicted_anomalies,
            labels,
        )
    )

    false_negatives = sum(
        not predicted and actual
        for predicted, actual in zip(
            predicted_anomalies,
            labels,
        )
    )

    precision_denominator = (
        true_positives + false_positives
    )
    recall_denominator = (
        true_positives + false_negatives
    )

    precision = (
        true_positives / precision_denominator
        if precision_denominator
        else 0.0
    )

    recall = (
        true_positives / recall_denominator
        if recall_denominator
        else 0.0
    )

    f1_denominator = precision + recall

    f1_score = (
        2 * precision * recall / f1_denominator
        if f1_denominator
        else 0.0
    )

    return EvaluationMetrics(
        true_positives=true_positives,
        false_positives=false_positives,
        true_negatives=true_negatives,
        false_negatives=false_negatives,
        precision=precision,
        recall=recall,
        f1_score=f1_score,
    )
"""Tests for anomaly-detection feature extraction."""

from datetime import datetime

from app.models.security_event import EventSeverity, SecurityEvent
from app.services.anomaly_detection.features import (
    EventFeatures,
    extract_event_features,
)


def test_extract_event_features() -> None:
    """A security event should produce the expected numerical features."""

    event = SecurityEvent(
        event_type="SSH_LOGIN_FAILURE",
        severity=EventSeverity.CRITICAL,
        source="linux-server-01",
        message="Failed password for root",
        user_id=42,
        telemetry_source_id=7,
        event_metadata={
            "source_ip": "203.0.113.10",
            "hostname": "linux-server-01",
        },
        occurred_at=datetime(2026, 10, 9, 23, 30),
        created_at=datetime(2026, 10, 10, 8, 0),
    )

    features = extract_event_features(event)

    assert features == EventFeatures(
        severity_score=3.0,
        hour_of_day=23.0,
        day_of_week=4.0,
        has_user=1.0,
        has_telemetry_source=1.0,
        metadata_field_count=2.0,
        message_length=float(len("Failed password for root")),
    )


def test_feature_vector_has_stable_order() -> None:
    """ML input order must remain deterministic."""

    features = EventFeatures(
        severity_score=3.0,
        hour_of_day=23.0,
        day_of_week=4.0,
        has_user=1.0,
        has_telemetry_source=1.0,
        metadata_field_count=2.0,
        message_length=24.0,
    )

    assert features.as_vector() == [
        3.0,
        23.0,
        4.0,
        1.0,
        1.0,
        2.0,
        24.0,
    ]


def test_feature_extraction_handles_optional_data() -> None:
    """Missing optional event data should still produce valid features."""

    event = SecurityEvent(
        event_type="SYSTEM_EVENT",
        severity=EventSeverity.INFO,
        source="server-01",
        message="Heartbeat",
        user_id=None,
        telemetry_source_id=None,
        event_metadata=None,
        occurred_at=None,
        created_at=datetime(2026, 10, 5, 8, 15),
    )

    features = extract_event_features(event)

    assert features.severity_score == 0.0
    assert features.hour_of_day == 8.0
    assert features.day_of_week == 0.0
    assert features.has_user == 0.0
    assert features.has_telemetry_source == 0.0
    assert features.metadata_field_count == 0.0
    assert features.message_length == 9.0
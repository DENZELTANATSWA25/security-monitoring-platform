"""Regression tests for production behavioural feature extraction."""

from datetime import datetime, timedelta, timezone

import pytest

from app.services.behavioural_detection.features import (
    BehaviourEventV2,
    BehaviourFeatureExtractorV2,
    FEATURE_NAMES,
    FEATURE_SCHEMA_VERSION,
)


BASE = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)


def make_event(
    seconds: int,
    *,
    user_id: str = "alice",
    source: str = "platform_authentication",
    success: bool | None = True,
    ip: str | None = "192.0.2.1",
    device: str | None = None,
) -> BehaviourEventV2:
    """Build a deterministic authentication event."""

    return BehaviourEventV2(
        timestamp=BASE + timedelta(seconds=seconds),
        source=source,
        event_type="authentication",
        user_id=user_id,
        authentication_success=success,
        ip_address=ip,
        device_id=device,
    )


def test_production_feature_schema_is_frozen() -> None:
    assert FEATURE_SCHEMA_VERSION == "behavioural-v2"
    assert len(FEATURE_NAMES) == 22

    vector = BehaviourFeatureExtractorV2().transform_one(
        make_event(0)
    )

    assert len(vector.as_vector()) == 22


def test_first_login_has_no_history() -> None:
    extractor = BehaviourFeatureExtractorV2()

    features = extractor.transform_one(make_event(0)).as_dict()

    assert features["source_events_5m"] == 0
    assert features["account_events_1h"] == 0
    assert features["account_new_ip"] == 0
    assert features["account_new_device"] == 0
    assert features["device_available"] == 0


def test_failed_logins_contribute_to_source_and_account_history() -> None:
    extractor = BehaviourFeatureExtractorV2()

    extractor.transform_one(make_event(0, success=False))
    extractor.transform_one(make_event(10, success=False))

    features = extractor.transform_one(
        make_event(20, success=True)
    ).as_dict()

    assert features["source_events_5m"] == 2
    assert features["source_failures_5m"] == 2
    assert features["source_failure_ratio_5m"] == pytest.approx(1.0)
    assert features["account_events_1h"] == 2
    assert features["account_failures_1h"] == 2


def test_source_history_includes_different_accounts() -> None:
    extractor = BehaviourFeatureExtractorV2()

    extractor.transform_one(make_event(0, user_id="alice"))
    extractor.transform_one(make_event(10, user_id="bob"))

    features = extractor.transform_one(
        make_event(20, user_id="charlie")
    ).as_dict()

    assert features["source_events_5m"] == 2
    assert features["source_distinct_users_1h"] == 2
    assert features["account_events_1h"] == 0


def test_new_ip_requires_previous_known_ip() -> None:
    extractor = BehaviourFeatureExtractorV2()

    extractor.transform_one(make_event(0, ip=None))

    first_known_ip = extractor.transform_one(
        make_event(10, ip="192.0.2.1")
    ).as_dict()

    assert first_known_ip["account_new_ip"] == 0

    changed_ip = extractor.transform_one(
        make_event(20, ip="192.0.2.2")
    ).as_dict()

    assert changed_ip["account_new_ip"] == 1


def test_equal_timestamps_do_not_leak_history() -> None:
    extractor = BehaviourFeatureExtractorV2()

    extractor.transform_one(make_event(0))

    features = extractor.transform_one(
        make_event(0, ip="192.0.2.2")
    ).as_dict()

    assert features["source_events_5m"] == 0
    assert features["account_events_1h"] == 0


def test_out_of_order_events_are_rejected() -> None:
    extractor = BehaviourFeatureExtractorV2()

    extractor.transform_one(make_event(20))

    with pytest.raises(ValueError, match="chronologically"):
        extractor.transform_one(make_event(10))


def test_events_expire_after_24_hours() -> None:
    extractor = BehaviourFeatureExtractorV2()

    extractor.transform_one(make_event(0))

    features = extractor.transform_one(
        make_event(86400)
    ).as_dict()

    assert features["source_events_24h"] == 0
    assert features["account_history_available"] == 0


def test_missing_device_is_explicitly_represented() -> None:
    features = BehaviourFeatureExtractorV2().transform_one(
        make_event(0, device=None)
    ).as_dict()

    assert features["device_available"] == 0
    assert features["account_new_device"] == 0
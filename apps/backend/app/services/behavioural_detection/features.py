"""Behavioural feature extraction v2.

Causal, bounded-history feature engineering for security events.

This module is independent of FastAPI, SQLAlchemy and scikit-learn.
It supports offline evaluation and future online integration.
"""

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Iterable
from math import isfinite
import ipaddress


FEATURE_SCHEMA_VERSION = "behavioural-v2"

WINDOWS = {
    "5m": 300,
    "1h": 3600,
    "24h": 86400,
}

FEATURE_NAMES = (
    "source_events_5m",
    "source_events_1h",
    "source_events_24h",
    "source_failures_5m",
    "source_failures_1h",
    "source_failures_24h",
    "source_failure_ratio_5m",
    "source_failure_ratio_1h",
    "source_failure_ratio_24h",
    "source_distinct_users_1h",
    "source_distinct_ips_1h",
    "account_events_1h",
    "account_failures_1h",
    "account_distinct_ips_24h",
    "account_new_ip",
    "account_new_device",
    "account_history_available",
    "seconds_since_source_event",
    "seconds_since_account_event",
    "ip_available",
    "device_available",
    "auth_outcome_available",
)


@dataclass(frozen=True)
class BehaviourEventV2:
    timestamp: datetime
    source: str
    event_type: str
    user_id: str | int | None = None
    authentication_success: bool | None = None
    ip_address: str | None = None
    device_id: str | None = None


@dataclass(frozen=True)
class BehaviourVectorV2:
    values: tuple[float, ...]

    def as_vector(self) -> list[float]:
        return list(self.values)

    def as_dict(self) -> dict[str, float]:
        return dict(zip(FEATURE_NAMES, self.values))


def normalize_timestamp(timestamp: datetime) -> datetime:
    if not isinstance(timestamp, datetime):
        raise TypeError("Timestamp must be a datetime.")

    if timestamp.tzinfo is None:
        # Matches the application's existing naive-UTC convention.
        timestamp = timestamp.replace(tzinfo=timezone.utc)

    return timestamp.astimezone(timezone.utc)


def normalize_ip(value: str | None) -> str | None:
    if value is None or not isinstance(value, str):
        return None

    try:
        return str(ipaddress.ip_address(value.strip()))
    except ValueError:
        # Invalid IP data is treated as unavailable, not suspicious.
        return None


def normalize_device(value: str | None) -> str | None:
    if not isinstance(value, str):
        return None

    value = value.strip()
    return value or None


class BehaviourFeatureExtractorV2:
    """Causal rolling-history extractor with a 24-hour retention cap.

    Histories are partitioned by source and user. This implementation
    assumes globally nondecreasing event timestamps.
    """

    def __init__(self):
        self._source_history = defaultdict(deque)
        self._account_history = defaultdict(deque)
        self._last_timestamp = None

    def _prune(self, history, timestamp):
        cutoff = timestamp - timedelta(seconds=WINDOWS["24h"])

        while history and history[0].timestamp <= cutoff:
            history.popleft()

    @staticmethod
    def _window(history, timestamp, seconds):
        cutoff = timestamp - timedelta(seconds=seconds)

        # Strictly earlier events only. Equal timestamps are excluded.
        return [
            item for item in history
            if cutoff < item.timestamp < timestamp
        ]

    @staticmethod
    def _failure_count(events):
        return sum(
            item.authentication_success is False
            for item in events
        )

    @staticmethod
    def _failure_ratio(events):
        # Unknown authentication outcomes are excluded from denominator.
        known = [
            item for item in events
            if type(item.authentication_success) is bool
        ]

        if not known:
            return 0.0

        return sum(
            item.authentication_success is False
            for item in known
        ) / len(known)

    def transform_one(
        self,
        event: BehaviourEventV2,
    ) -> BehaviourVectorV2:
        timestamp = normalize_timestamp(event.timestamp)

        source = event.source.strip()

        if not source:
            raise ValueError("Event source cannot be empty.")

        if self._last_timestamp is not None:
            if timestamp < self._last_timestamp:
                raise ValueError(
                    "Events must be processed chronologically."
                )

        # Validate before mutating extractor state.
        if type(event.authentication_success) not in (bool, type(None)):
            raise ValueError(
                "Authentication outcome must be bool or None."
            )

        user_key = (
            str(event.user_id)
            if event.user_id is not None
            else None
        )

        ip_address = normalize_ip(event.ip_address)
        device_id = normalize_device(event.device_id)

        source_history = self._source_history[source]
        self._prune(source_history, timestamp)

        if user_key is not None:
            account_history = self._account_history[user_key]
            self._prune(account_history, timestamp)
        else:
            account_history = ()

        s5 = self._window(
            source_history, timestamp, WINDOWS["5m"]
        )
        s1h = self._window(
            source_history, timestamp, WINDOWS["1h"]
        )
        s24h = self._window(
            source_history, timestamp, WINDOWS["24h"]
        )

        a1h = self._window(
            account_history, timestamp, WINDOWS["1h"]
        )
        a24h = self._window(
            account_history, timestamp, WINDOWS["24h"]
        )

        account_history_available = bool(a24h)

        known_ips = {
            item.ip_address
            for item in a24h
            if item.ip_address is not None
        }

        known_devices = {
            item.device_id
            for item in a24h
            if item.device_id is not None
        }

        # A first observation is not automatically suspicious.
        new_ip = (
            user_key is not None
            and ip_address is not None
            and bool(known_ips)
            and ip_address not in known_ips
        )

        new_device = (
            user_key is not None
            and device_id is not None
            and bool(known_devices)
            and device_id not in known_devices
        )

        source_elapsed = (
            (timestamp - s24h[-1].timestamp).total_seconds()
            if s24h else float(WINDOWS["24h"])
        )

        account_elapsed = (
            (timestamp - a24h[-1].timestamp).total_seconds()
            if a24h else float(WINDOWS["24h"])
        )

        values = (
            float(len(s5)),
            float(len(s1h)),
            float(len(s24h)),
            float(self._failure_count(s5)),
            float(self._failure_count(s1h)),
            float(self._failure_count(s24h)),
            self._failure_ratio(s5),
            self._failure_ratio(s1h),
            self._failure_ratio(s24h),
            float(len({
                item.user_id for item in s1h
                if item.user_id is not None
            })),
            float(len({
                item.ip_address for item in s1h
                if item.ip_address is not None
            })),
            float(len(a1h)),
            float(self._failure_count(a1h)),
            float(len(known_ips)),
            float(new_ip),
            float(new_device),
            float(account_history_available),
            float(source_elapsed),
            float(account_elapsed),
            float(ip_address is not None),
            float(device_id is not None),
            float(event.authentication_success is not None),
        )

        if len(values) != len(FEATURE_NAMES):
            raise RuntimeError("Feature schema length mismatch.")

        if not all(isfinite(value) for value in values):
            raise ValueError("Non-finite feature value.")

        normalized = BehaviourEventV2(
            timestamp=timestamp,
            source=source,
            event_type=event.event_type,
            user_id=user_key,
            authentication_success=event.authentication_success,
            ip_address=ip_address,
            device_id=device_id,
        )

        # State is updated only after features have been calculated.
        source_history.append(normalized)

        if user_key is not None:
            self._account_history[user_key].append(normalized)

        self._last_timestamp = timestamp

        return BehaviourVectorV2(values=values)

    def transform(
        self,
        events: Iterable[BehaviourEventV2],
    ) -> list[BehaviourVectorV2]:
        return [self.transform_one(event) for event in events]

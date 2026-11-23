
"""Database-backed behavioural features for first-party login attempts."""

from datetime import timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.login_attempt import LoginAttempt
from app.services.behavioural_detection.features import (
    BehaviourEventV2,
    BehaviourFeatureExtractorV2,
    BehaviourVectorV2,
    normalize_timestamp,
    normalize_ip,
    normalize_device,
)


AUTHENTICATION_SOURCE = "platform_authentication"
HISTORY_SECONDS = 86400

class BehaviouralFeatureError(ValueError):
    """Invalid data prevents reliable behavioural feature extraction."""


def login_attempt_to_event(
    attempt: LoginAttempt,
) -> BehaviourEventV2:
    """Convert a persisted login attempt into the frozen input schema."""

    try:
        if attempt.timestamp is None:
            raise ValueError("Missing login timestamp.")

        email = attempt.email.strip().casefold()

        if not email:
            raise ValueError("Missing account identifier.")

        ip = attempt.ip_address

        if ip is not None:
            ip = ip.strip()

        if not ip or ip == "0.0.0.0":
            ip = None

        return BehaviourEventV2(
            timestamp=normalize_timestamp(attempt.timestamp),
            source=AUTHENTICATION_SOURCE,
            event_type="authentication",
            user_id=email,
            authentication_success=attempt.successful,
            ip_address=ip,
            device_id=None,
        )

    except (ValueError, TypeError, AttributeError) as exc:
        raise BehaviouralFeatureError(
            "Login attempt cannot be converted to behavioural features."
        ) from exc


def build_extractor_from_history(
    history: list[LoginAttempt],
) -> BehaviourFeatureExtractorV2:
    """Restore chronological history without computing unused vectors.

    Normalisation and validation mirror the frozen extractor's
    transform_one() behaviour for historical authentication events.
    """

    extractor = BehaviourFeatureExtractorV2()
    last_timestamp = None

    for attempt in history:
        event = login_attempt_to_event(attempt)
        timestamp = event.timestamp

        source = event.source.strip()

        if not source:
            raise BehaviouralFeatureError(
                "Login history contains an invalid source."
            )

        if last_timestamp is not None and timestamp < last_timestamp:
            raise BehaviouralFeatureError(
                "Login history is not chronological."
            )

        # Preserve the frozen extractor's strict outcome validation.
        if type(event.authentication_success) not in (bool, type(None)):
            raise BehaviouralFeatureError(
                "Invalid historical authentication outcome."
            )

        user_key = (
            str(event.user_id)
            if event.user_id is not None
            else None
        )

        # Match the frozen extractor's IP and device normalisation.

        normalized = BehaviourEventV2(
            timestamp=timestamp,
            source=source,
            event_type=event.event_type,
            user_id=user_key,
            authentication_success=event.authentication_success,
            ip_address=normalize_ip(event.ip_address),
            device_id=normalize_device(event.device_id),
        )

        extractor._source_history[source].append(normalized)

        if user_key is not None:
            extractor._account_history[user_key].append(normalized)

        last_timestamp = timestamp

    extractor._last_timestamp = last_timestamp

    return extractor


async def extract_login_behaviour(
    db: AsyncSession,
    attempt: LoginAttempt,
) -> BehaviourVectorV2:
    """Reconstruct causal history and extract the current login vector.

    The current attempt must already have been flushed to the database.
    This function performs no commits or writes.
    """

    if attempt.id is None or attempt.timestamp is None:
        raise BehaviouralFeatureError(
            "Login attempt must be flushed before extraction."
        )

    current = login_attempt_to_event(attempt)
    timestamp = current.timestamp

    # Existing PostgreSQL timestamps use naive UTC.
    database_timestamp = timestamp.replace(tzinfo=None)
    cutoff = database_timestamp - timedelta(
        seconds=HISTORY_SECONDS
    )

    statement = (
        select(LoginAttempt)
        .where(
            LoginAttempt.timestamp > cutoff,
            LoginAttempt.timestamp < database_timestamp,
            LoginAttempt.id != attempt.id,
        )
        .order_by(
            LoginAttempt.timestamp.asc(),
            LoginAttempt.id.asc(),
        )
    )

    result = await db.execute(statement)
    history = result.scalars().all()

    try:
        # Rebuild state in O(n) instead of recalculating every
        # intermediate historical feature vector.
        extractor = build_extractor_from_history(history)

        # Only the current attempt needs a 22-feature vector.
        return extractor.transform_one(current)

    except (ValueError, TypeError, AttributeError) as exc:
        raise BehaviouralFeatureError(
            "Behavioural history cannot be reconstructed."
        ) from exc

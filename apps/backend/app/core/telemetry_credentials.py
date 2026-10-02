"""Credential utilities for external telemetry producers."""

import hashlib
import hmac
import secrets
from dataclasses import dataclass


CREDENTIAL_PREFIX = "smp"
KEY_ID_BYTES = 12
SECRET_BYTES = 32


@dataclass(frozen=True)
class TelemetryCredential:
    """Components of a newly generated telemetry credential."""

    key_id: str
    secret: str
    credential: str


def hash_telemetry_secret(secret: str) -> str:
    """
    Hash a high-entropy telemetry secret for storage.

    Telemetry secrets are randomly generated rather than human chosen,
    so SHA-256 provides a deterministic representation suitable for
    secure verification without storing the plaintext secret.
    """

    return hashlib.sha256(
        secret.encode("utf-8"),
    ).hexdigest()


def generate_telemetry_credential() -> TelemetryCredential:
    """
    Generate a new machine-to-machine telemetry credential.

    The complete credential is intended to be returned to the producer
    only when it is created. Only the key identifier and secret hash
    should be persisted.
    """

    key_id = secrets.token_hex(KEY_ID_BYTES)
    secret = secrets.token_urlsafe(SECRET_BYTES)

    credential = f"{CREDENTIAL_PREFIX}_{key_id}.{secret}"

    return TelemetryCredential(
        key_id=key_id,
        secret=secret,
        credential=credential,
    )


def parse_telemetry_credential(
    credential: str,
) -> tuple[str, str] | None:
    """Parse a telemetry credential into its key identifier and secret."""

    prefix = f"{CREDENTIAL_PREFIX}_"

    if not credential.startswith(prefix):
        return None

    body = credential[len(prefix):]

    try:
        key_id, secret = body.split(".", 1)
    except ValueError:
        return None

    if not key_id or not secret:
        return None

    return key_id, secret


def verify_telemetry_secret(
    secret: str,
    expected_hash: str,
) -> bool:
    """Verify a telemetry secret using a timing-safe comparison."""

    actual_hash = hash_telemetry_secret(secret)

    return hmac.compare_digest(
        actual_hash,
        expected_hash,
    )
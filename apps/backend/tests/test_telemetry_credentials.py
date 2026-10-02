"""Tests for telemetry producer credential utilities."""

from app.core.telemetry_credentials import (
    generate_telemetry_credential,
    hash_telemetry_secret,
    parse_telemetry_credential,
    verify_telemetry_secret,
)


def test_generated_credential_can_be_parsed() -> None:
    credential = generate_telemetry_credential()

    parsed = parse_telemetry_credential(
        credential.credential,
    )

    assert parsed is not None

    key_id, secret = parsed

    assert key_id == credential.key_id
    assert secret == credential.secret


def test_generated_credentials_are_unique() -> None:
    first = generate_telemetry_credential()
    second = generate_telemetry_credential()

    assert first.key_id != second.key_id
    assert first.secret != second.secret
    assert first.credential != second.credential


def test_secret_hash_is_deterministic() -> None:
    secret = "high-entropy-test-secret"

    assert (
        hash_telemetry_secret(secret)
        == hash_telemetry_secret(secret)
    )


def test_valid_secret_is_verified() -> None:
    secret = "correct-secret"

    stored_hash = hash_telemetry_secret(secret)

    assert verify_telemetry_secret(
        secret,
        stored_hash,
    )


def test_invalid_secret_is_rejected() -> None:
    stored_hash = hash_telemetry_secret(
        "correct-secret",
    )

    assert not verify_telemetry_secret(
        "incorrect-secret",
        stored_hash,
    )


def test_malformed_credentials_are_rejected() -> None:
    invalid_credentials = [
        "",
        "random-string",
        "smp_",
        "smp_key-without-secret",
        "smp_.secret",
        "wrong_key.secret",
    ]

    for credential in invalid_credentials:
        assert (
            parse_telemetry_credential(credential)
            is None
        )
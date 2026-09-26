"""Password hashing and verification tests."""

import bcrypt

from app.core.security import hash_password, verify_password


TEST_PASSWORD = "SecurePassword123!"


def test_hash_password_does_not_store_plaintext() -> None:
    """Passwords must never be returned or stored as plaintext."""

    hashed_password = hash_password(TEST_PASSWORD)

    assert hashed_password != TEST_PASSWORD


def test_hash_password_creates_bcrypt_hash() -> None:
    """New password hashes must use the bcrypt format."""

    hashed_password = hash_password(TEST_PASSWORD)

    assert hashed_password.startswith(("$2a$", "$2b$", "$2y$"))


def test_verify_password_accepts_correct_password() -> None:
    """The original password must verify against its hash."""

    hashed_password = hash_password(TEST_PASSWORD)

    assert verify_password(
        TEST_PASSWORD,
        hashed_password,
    ) is True


def test_verify_password_rejects_wrong_password() -> None:
    """An incorrect password must not verify."""

    hashed_password = hash_password(TEST_PASSWORD)

    assert verify_password(
        "WrongPassword123!",
        hashed_password,
    ) is False


def test_verify_password_accepts_existing_bcrypt_hash() -> None:
    """
    Existing bcrypt hashes must remain usable after the hashing
    implementation is changed.
    """

    existing_hash = bcrypt.hashpw(
        TEST_PASSWORD.encode("utf-8"),
        bcrypt.gensalt(),
    ).decode("utf-8")

    assert verify_password(
        TEST_PASSWORD,
        existing_hash,
    ) is True


def test_same_password_produces_different_hashes() -> None:
    """bcrypt must use a unique salt when hashing passwords."""

    first_hash = hash_password(TEST_PASSWORD)
    second_hash = hash_password(TEST_PASSWORD)

    assert first_hash != second_hash

def test_pytest_is_working():
    """
    Verify that the project's pytest test runner is configured correctly.

    This is intentionally simple. It gives us a known-good test before
    introducing databases, HTTP clients, authentication, or async code.
    """

    # Arrange
    expected = "Security Monitoring Platform"

    # Act
    actual = "Security Monitoring Platform"

    # Assert
    assert actual == expected

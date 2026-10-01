"""Tests for IP-based location resolution."""

from types import SimpleNamespace
from unittest.mock import MagicMock

from geoip2.errors import AddressNotFoundError

from app.core.config import settings
from app.services.location_service import (
    GeoLocation,
    is_public_ip,
    resolve_ip_location,
)

def test_public_ip_is_accepted() -> None:
    """Globally routable addresses are eligible for GeoIP resolution."""

    assert is_public_ip("8.8.8.8") is True


def test_private_ip_is_rejected() -> None:
    """Private network addresses must not be geolocated."""

    assert is_public_ip("192.168.1.10") is False


def test_loopback_ip_is_rejected() -> None:
    """Loopback addresses must not be geolocated."""

    assert is_public_ip("127.0.0.1") is False


def test_invalid_ip_is_rejected() -> None:
    """Malformed values must fail safely."""

    assert is_public_ip("not-an-ip-address") is False


async def test_unconfigured_resolver_returns_no_location(
    monkeypatch,
) -> None:
    """Location resolution should fail safely when no provider exists."""

    monkeypatch.setattr(
        settings,
        "GEOIP_DATABASE_PATH",
        None,
    )

    result = await resolve_ip_location("8.8.8.8")

    assert result is None

async def test_resolver_returns_location_from_geoip_database(
    monkeypatch,
) -> None:
    """A valid GeoIP database result should return coordinates."""

    monkeypatch.setattr(
        settings,
        "GEOIP_DATABASE_PATH",
        "/fake/GeoLite2-City.mmdb",
    )

    response = SimpleNamespace(
        location=SimpleNamespace(
            latitude=51.5074,
            longitude=-0.1278,
        )
    )

    reader = MagicMock()
    reader.city.return_value = response

    reader_context = MagicMock()
    reader_context.__enter__.return_value = reader
    reader_context.__exit__.return_value = False

    monkeypatch.setattr(
        "app.services.location_service.geoip2.database.Reader",
        lambda path: reader_context,
    )

    result = await resolve_ip_location("8.8.8.8")

    assert result == GeoLocation(
        latitude=51.5074,
        longitude=-0.1278,
    )

    reader.city.assert_called_once_with("8.8.8.8")


async def test_resolver_returns_none_when_address_not_found(
    monkeypatch,
) -> None:
    """An IP missing from the GeoIP database should fail safely."""

    monkeypatch.setattr(
        settings,
        "GEOIP_DATABASE_PATH",
        "/fake/GeoLite2-City.mmdb",
    )

    reader = MagicMock()
    reader.city.side_effect = AddressNotFoundError(
        "Address not found",
    )

    reader_context = MagicMock()
    reader_context.__enter__.return_value = reader
    reader_context.__exit__.return_value = False

    monkeypatch.setattr(
        "app.services.location_service.geoip2.database.Reader",
        lambda path: reader_context,
    )

    result = await resolve_ip_location("8.8.8.8")

    assert result is None


async def test_resolver_returns_none_for_missing_coordinates(
    monkeypatch,
) -> None:
    """GeoIP records without coordinates should fail safely."""

    monkeypatch.setattr(
        settings,
        "GEOIP_DATABASE_PATH",
        "/fake/GeoLite2-City.mmdb",
    )

    response = SimpleNamespace(
        location=SimpleNamespace(
            latitude=None,
            longitude=None,
        )
    )

    reader = MagicMock()
    reader.city.return_value = response

    reader_context = MagicMock()
    reader_context.__enter__.return_value = reader
    reader_context.__exit__.return_value = False

    monkeypatch.setattr(
        "app.services.location_service.geoip2.database.Reader",
        lambda path: reader_context,
    )

    result = await resolve_ip_location("8.8.8.8")

    assert result is None


async def test_resolver_rejects_invalid_coordinates(
    monkeypatch,
) -> None:
    """Coordinates outside valid geographic ranges should be rejected."""

    monkeypatch.setattr(
        settings,
        "GEOIP_DATABASE_PATH",
        "/fake/GeoLite2-City.mmdb",
    )

    response = SimpleNamespace(
        location=SimpleNamespace(
            latitude=95.0,
            longitude=-0.1278,
        )
    )

    reader = MagicMock()
    reader.city.return_value = response

    reader_context = MagicMock()
    reader_context.__enter__.return_value = reader
    reader_context.__exit__.return_value = False

    monkeypatch.setattr(
        "app.services.location_service.geoip2.database.Reader",
        lambda path: reader_context,
    )

    result = await resolve_ip_location("8.8.8.8")

    assert result is None
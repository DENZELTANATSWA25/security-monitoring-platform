"""IP-based geographic location resolution."""

from dataclasses import dataclass
from ipaddress import ip_address

import geoip2.database
from geoip2.errors import AddressNotFoundError

from app.core.config import settings


@dataclass(frozen=True)
class GeoLocation:
    """Geographic coordinates associated with an IP address."""

    latitude: float
    longitude: float


def is_public_ip(value: str) -> bool:
    """
    Return whether an IP address is suitable for geographic resolution.

    Invalid, loopback, private, link-local, multicast, reserved, and
    unspecified addresses are intentionally excluded.
    """
    try:
        parsed_ip = ip_address(value)
    except ValueError:
        return False

    return parsed_ip.is_global


async def resolve_ip_location(
    value: str | None,
) -> GeoLocation | None:
    """
    Resolve a public IP address to geographic coordinates.

    GeoIP enrichment is optional. Invalid or non-public addresses, an
    unconfigured database, addresses missing from the database, malformed
    location records, and database access failures all return None so that
    authentication remains available.
    """
    if value is None or not is_public_ip(value):
        return None

    database_path = settings.GEOIP_DATABASE_PATH

    if not database_path:
        return None

    try:
        with geoip2.database.Reader(database_path) as reader:
            response = reader.city(value)

            latitude = response.location.latitude
            longitude = response.location.longitude

    except (AddressNotFoundError, OSError, ValueError):
        return None

    if latitude is None or longitude is None:
        return None

    if not (-90.0 <= latitude <= 90.0):
        return None

    if not (-180.0 <= longitude <= 180.0):
        return None

    return GeoLocation(
        latitude=float(latitude),
        longitude=float(longitude),
    )
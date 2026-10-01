# Geographic utilities used by location-based detection rules.

from math import asin, cos, radians, sin, sqrt

EARTH_RADIUS_KM = 6371.088

def haversine_distance_km(
        latitude_1: float,
        longitude_1: float,
        latitude_2: float,
        longitude_2: float,
) -> float:
    """
    Calculate the great-circle distance between two geographic coordinates.

    Coordinates are expressed in decimal degrees and returned distance is expressed in kilometers.
    """
    latitude_1_rad = radians(latitude_1)
    longitude_1_rad = radians(longitude_1)
    latitude_2_rad = radians(latitude_2)
    longitude_2_rad = radians(longitude_2)

    latitude_delta = latitude_2_rad - latitude_1_rad
    longitude_delta = longitude_2_rad - longitude_1_rad

    haversine_value = (
        sin(latitude_delta / 2) ** 2
        + cos(latitude_1_rad)
        * cos(latitude_2_rad)
        * sin(longitude_delta / 2) ** 2
    )

    angular_distance = 2 * asin(
        sqrt(haversine_value)
    )

    return EARTH_RADIUS_KM * angular_distance
"""
Coordinate Transformation System for Charlotte Digital Twin

Converts between geographic coordinate systems:
- WGS84 (lat/lon) - GPS coordinates
- UTM Zone 17N (easting/northing) - Projected coordinates
- Blender World (x/y/z) - Scene coordinates

Usage:
    from lib.charlotte_digital_twin.geometry import CoordinateTransformer, GeometryConfig

    config = GeometryConfig()
    transformer = CoordinateTransformer(config)

    # Convert single coordinate
    world = transformer.latlon_to_world(35.2280, -80.8420)
    print(f"World position: {world.x}, {world.y}, {world.z}")

    # Convert multiple coordinates
    coords = [(35.2280, -80.8420), (35.2290, -80.8410)]
    world_coords = transformer.latlon_to_world_batch(coords)
"""

import math
from typing import List, Optional, Tuple, Union

from .types import (
    GeometryConfig,
    GeoCoordinate,
    UTMCoordinate,
    WorldCoordinate,
    SceneOrigin,
)


class CoordinateTransformer:
    """
    Transforms coordinates between geographic and Blender world systems.

    Uses a local tangent plane approximation centered on the scene origin.
    This is accurate to within ~1 meter for areas up to ~10km from origin.

    For Charlotte (35.2°N), 1 degree latitude ≈ 111 km, 1 degree longitude ≈ 91 km.
    """

    # Earth parameters
    EARTH_RADIUS_M = 6378137.0  # WGS84 semi-major axis in meters
    EARTH_FLATTENING = 1 / 298.257223563

    # Conversion factors
    DEG_TO_RAD = math.pi / 180.0
    RAD_TO_DEG = 180.0 / math.pi

    def __init__(self, config: Optional[GeometryConfig] = None):
        """
        Initialize transformer with configuration.

        Args:
            config: Geometry configuration with scene origin
        """
        self.config = config or GeometryConfig()
        self.origin = self.config.origin

        # Pre-calculate origin values for efficiency
        self._origin_lat_rad = self.origin.lat * self.DEG_TO_RAD
        self._origin_lon_rad = self.origin.lon * self.DEG_TO_RAD

        # Calculate UTM coordinates of origin
        self._origin_utm = self._latlon_to_utm(
            self.origin.lat,
            self.origin.lon,
            self.origin.utm_zone
        )

        # Calculate meters per degree at origin latitude
        # Latitude: ~111 km per degree everywhere
        self._meters_per_deg_lat = 111132.92 - 559.82 * math.cos(2 * self._origin_lat_rad) + \
                                   1.175 * math.cos(4 * self._origin_lat_rad)

        # Longitude: varies with latitude (cos(lat) * 111.32 km at equator)
        self._meters_per_deg_lon = 111412.84 * math.cos(self._origin_lat_rad) - \
                                   93.5 * math.cos(3 * self._origin_lat_rad) + \
                                   0.118 * math.cos(5 * self._origin_lat_rad)

    def latlon_to_world(
        self,
        lat: float,
        lon: float,
        elevation: float = 0.0,
    ) -> WorldCoordinate:
        """
        Convert WGS84 lat/lon to Blender world coordinates.

        The conversion uses a local tangent plane approximation:
        - X = meters east of origin
        - Y = meters north of origin
        - Z = elevation relative to origin elevation

        Args:
            lat: Latitude in degrees
            lon: Longitude in degrees
            elevation: Elevation in meters (default 0)

        Returns:
            WorldCoordinate with x, y, z in meters from origin
        """
        # Calculate delta in degrees
        delta_lat = lat - self.origin.lat
        delta_lon = lon - self.origin.lon

        # Convert to meters using local approximation
        x = delta_lon * self._meters_per_deg_lon  # East-West
        y = delta_lat * self._meters_per_deg_lat  # North-South

        # Z is elevation relative to origin
        z = elevation - self.origin.elevation if elevation else 0.0

        # Apply scale
        scale = self.config.scale
        x *= scale
        y *= scale
        z *= scale

        # Apply Z offset
        z += self.config.z_offset

        # Flatten to plane if configured
        if self.config.flatten_to_plane:
            z = self.config.z_offset

        return WorldCoordinate(x, y, z)

    def latlon_to_world_batch(
        self,
        coords: List[Union[Tuple[float, float], Tuple[float, float, float]]],
    ) -> List[WorldCoordinate]:
        """
        Convert multiple coordinates at once.

        Args:
            coords: List of (lat, lon) or (lat, lon, elevation) tuples

        Returns:
            List of WorldCoordinate objects
        """
        results = []
        for coord in coords:
            if len(coord) == 2:
                lat, lon = coord
                elevation = 0.0
            else:
                lat, lon, elevation = coord
            results.append(self.latlon_to_world(lat, lon, elevation))
        return results

    def world_to_latlon(
        self,
        x: float,
        y: float,
        z: float = 0.0,
    ) -> GeoCoordinate:
        """
        Convert Blender world coordinates back to WGS84 lat/lon.

        Args:
            x: X coordinate in meters from origin
            y: Y coordinate in meters from origin
            z: Z coordinate (elevation offset)

        Returns:
            GeoCoordinate with lat, lon, elevation
        """
        # Reverse scale
        scale = self.config.scale
        x /= scale
        y /= scale
        z = (z - self.config.z_offset) / scale

        # Reverse Z offset for elevation
        elevation = z + self.origin.elevation

        # Convert meters to degrees
        delta_lon = x / self._meters_per_deg_lon
        delta_lat = y / self._meters_per_deg_lat

        lat = self.origin.lat + delta_lat
        lon = self.origin.lon + delta_lon

        return GeoCoordinate(lat, lon, elevation)

    def _latlon_to_utm(
        self,
        lat: float,
        lon: float,
        zone: int,
    ) -> UTMCoordinate:
        """
        Convert WGS84 lat/lon to UTM coordinates.

        Uses standard UTM projection formulas.

        Args:
            lat: Latitude in degrees
            lon: Longitude in degrees
            zone: UTM zone number

        Returns:
            UTMCoordinate with easting, northing, zone, hemisphere
        """
        # Convert to radians
        lat_rad = lat * self.DEG_TO_RAD
        lon_rad = lon * self.DEG_TO_RAD

        # UTM parameters
        k0 = 0.9996  # Scale factor

        # Reference meridian for zone
        lon0 = (zone - 1) * 6 - 180 + 3  # Central meridian
        lon0_rad = lon0 * self.DEG_TO_RAD

        # Ellipsoid parameters
        a = self.EARTH_RADIUS_M
        f = self.EARTH_FLATTENING
        e = math.sqrt(2 * f - f * f)  # Eccentricity

        # Prime vertical radius of curvature
        N = a / math.sqrt(1 - e * e * math.sin(lat_rad) ** 2)

        # Tangent of latitude
        T = math.tan(lat_rad) ** 2

        # Param C
        C = e * e * math.cos(lat_rad) ** 2 / (1 - e * e)

        # Longitude difference
        A = (lon_rad - lon0_rad) * math.cos(lat_rad)

        # M - true distance along central meridian from equator to lat
        M = a * (
            (1 - e * e / 4 - 3 * e ** 4 / 64 - 5 * e ** 6 / 256) * lat_rad
            - (3 * e * e / 8 + 3 * e ** 4 / 32 + 45 * e ** 6 / 1024) * math.sin(2 * lat_rad)
            + (15 * e ** 4 / 256 + 45 * e ** 6 / 1024) * math.sin(4 * lat_rad)
            - (35 * e ** 6 / 3072) * math.sin(6 * lat_rad)
        )

        # UTM coordinates
        easting = k0 * N * (
            A
            + (1 - T + C) * A ** 3 / 6
            + (5 - 18 * T + T ** 2 + 72 * C - 58 * e ** 2) * A ** 5 / 120
        ) + 500000  # False easting

        northing = k0 * (
            M
            + N * math.tan(lat_rad) * (
                A ** 2 / 2
                + (5 - T + 9 * C + 4 * C ** 2) * A ** 4 / 24
                + (61 - 58 * T + T ** 2 + 600 * C - 330 * e ** 2) * A ** 6 / 720
            )
        )

        # Southern hemisphere adjustment
        hemisphere = "N"
        if lat < 0:
            northing += 10000000  # False northing for southern hemisphere
            hemisphere = "S"

        return UTMCoordinate(easting, northing, zone, hemisphere)

    def utm_to_latlon(
        self,
        easting: float,
        northing: float,
        zone: int,
        hemisphere: str = "N",
    ) -> GeoCoordinate:
        """
        Convert UTM coordinates to WGS84 lat/lon.

        Args:
            easting: UTM easting in meters
            northing: UTM northing in meters
            zone: UTM zone number
            hemisphere: N or S

        Returns:
            GeoCoordinate with lat, lon, elevation
        """
        # UTM parameters
        k0 = 0.9996

        # Ellipsoid parameters
        a = self.EARTH_RADIUS_M
        f = self.EARTH_FLATTENING
        e = math.sqrt(2 * f - f * f)

        # Reference meridian
        lon0 = (zone - 1) * 6 - 180 + 3

        # Adjust for southern hemisphere
        y = northing
        if hemisphere == "S":
            y -= 10000000

        # Calculate footpoint latitude
        e1 = (1 - math.sqrt(1 - e * e)) / (1 + math.sqrt(1 - e * e))
        M = y / k0
        mu = M / (a * (1 - e * e / 4 - 3 * e ** 4 / 64 - 5 * e ** 6 / 256))

        phi1 = mu + (
            3 * e1 / 2 - 27 * e1 ** 3 / 32
        ) * math.sin(2 * mu) + (
            21 * e1 ** 2 / 16 - 55 * e1 ** 4 / 32
        ) * math.sin(4 * mu) + (
            151 * e1 ** 3 / 96
        ) * math.sin(6 * mu) + (
            1097 * e1 ** 4 / 512
        ) * math.sin(8 * mu)

        phi1_rad = phi1

        # Calculate other terms
        N1 = a / math.sqrt(1 - e * e * math.sin(phi1_rad) ** 2)
        T1 = math.tan(phi1_rad) ** 2
        C1 = e * e * math.cos(phi1_rad) ** 2 / (1 - e * e)
        R1 = a * (1 - e * e) / (1 - e * e * math.sin(phi1_rad) ** 2) ** 1.5
        D = (easting - 500000) / (N1 * k0)

        # Calculate latitude
        lat = phi1_rad - (
            N1 * math.tan(phi1_rad) / R1
        ) * (
            D ** 2 / 2
            - (5 + 3 * T1 + 10 * C1 - 4 * C1 ** 2 - 9 * e * e) * D ** 4 / 24
            + (61 + 90 * T1 + 298 * C1 + 45 * T1 ** 2 - 252 * e * e - 3 * C1 ** 2) * D ** 6 / 720
        )

        # Calculate longitude
        lon = (
            D
            - (1 + 2 * T1 + C1) * D ** 3 / 6
            + (5 - 2 * C1 + 28 * T1 - 3 * C1 ** 2 + 8 * e * e + 24 * T1 ** 2) * D ** 5 / 120
        ) / math.cos(phi1_rad)

        lon += lon0 * self.DEG_TO_RAD

        # Convert to degrees
        lat_deg = lat * self.RAD_TO_DEG
        lon_deg = lon * self.RAD_TO_DEG

        return GeoCoordinate(lat_deg, lon_deg, 0.0)

    def get_distance_meters(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        """
        Calculate distance between two lat/lon points in meters.

        Uses Haversine formula for accuracy.

        Args:
            lat1, lon1: First point
            lat2, lon2: Second point

        Returns:
            Distance in meters
        """
        # Convert to radians
        lat1_rad = lat1 * self.DEG_TO_RAD
        lat2_rad = lat2 * self.DEG_TO_RAD
        delta_lat = (lat2 - lat1) * self.DEG_TO_RAD
        delta_lon = (lon2 - lon1) * self.DEG_TO_RAD

        # Haversine formula
        a = (
            math.sin(delta_lat / 2) ** 2 +
            math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

        return self.EARTH_RADIUS_M * c

    def get_bearing_degrees(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        """
        Calculate bearing from point 1 to point 2 in degrees.

        Args:
            lat1, lon1: Start point
            lat2, lon2: End point

        Returns:
            Bearing in degrees (0 = North, 90 = East)
        """
        # Convert to radians
        lat1_rad = lat1 * self.DEG_TO_RAD
        lat2_rad = lat2 * self.DEG_TO_RAD
        delta_lon = (lon2 - lon1) * self.DEG_TO_RAD

        # Calculate bearing
        x = math.sin(delta_lon) * math.cos(lat2_rad)
        y = math.cos(lat1_rad) * math.sin(lat2_rad) - \
            math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(delta_lon)

        bearing = math.atan2(x, y) * self.RAD_TO_DEG

        # Normalize to 0-360
        return (bearing + 360) % 360


# Preset origins for Charlotte landmarks
CHARLOTTE_ORIGINS = {
    "downtown": SceneOrigin(
        lat=35.2271,
        lon=-80.8431,
        name="Charlotte Downtown",
        elevation=230.0,
    ),
    "airport": SceneOrigin(
        lat=35.2140,
        lon=-80.9431,
        name="Charlotte Douglas Airport",
        elevation=228.0,
    ),
    "uncc": SceneOrigin(
        lat=35.3075,
        lon=-80.7337,
        name="UNC Charlotte",
        elevation=235.0,
    ),
    "southpark": SceneOrigin(
        lat=35.1517,
        lon=-80.8095,
        name="SouthPark Mall",
        elevation=250.0,
    ),
    "noda": SceneOrigin(
        lat=35.2557,
        lon=-80.8153,
        name="NoDa Arts District",
        elevation=240.0,
    ),
}


__all__ = [
    "CoordinateTransformer",
    "CHARLOTTE_ORIGINS",
]

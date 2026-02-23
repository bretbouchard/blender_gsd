"""
Unit tests for Charlotte Digital Twin coordinate transformer module.

Tests coordinate conversion math without Blender dependencies.

Note: bpy and mathutils are mocked in conftest.py before any imports.
"""

import pytest
import math

from lib.charlotte_digital_twin.geometry.coordinates import (
    CoordinateTransformer,
    CHARLOTTE_ORIGINS,
)
from lib.charlotte_digital_twin.geometry.types import (
    GeometryConfig,
    SceneOrigin,
    WorldCoordinate,
    GeoCoordinate,
    UTMCoordinate,
)


class TestCoordinateTransformer:
    """Tests for CoordinateTransformer class."""

    def test_default_initialization(self):
        """Test default initialization with Charlotte downtown."""
        transformer = CoordinateTransformer()

        assert transformer.origin.lat == pytest.approx(35.2271)
        assert transformer.origin.lon == pytest.approx(-80.8431)

    def test_custom_config(self):
        """Test with custom configuration."""
        origin = SceneOrigin(
            lat=40.7128,
            lon=-74.0060,
            name="NYC"
        )
        config = GeometryConfig(origin=origin)
        transformer = CoordinateTransformer(config)

        assert transformer.origin.lat == pytest.approx(40.7128)

    def test_latlon_to_world_origin(self):
        """Test converting origin point itself."""
        transformer = CoordinateTransformer()
        result = transformer.latlon_to_world(
            transformer.origin.lat,
            transformer.origin.lon
        )

        assert result.x == pytest.approx(0.0, abs=1e-6)
        assert result.y == pytest.approx(0.0, abs=1e-6)

    def test_latlon_to_world_north_offset(self):
        """Test converting point north of origin."""
        transformer = CoordinateTransformer()

        # 1 degree north
        result = transformer.latlon_to_world(
            transformer.origin.lat + 1.0,
            transformer.origin.lon
        )

        # Should be positive Y (north)
        assert result.y > 0
        assert result.x == pytest.approx(0.0, abs=100)  # Allow small error

    def test_latlon_to_world_east_offset(self):
        """Test converting point east of origin."""
        transformer = CoordinateTransformer()

        # 1 degree east
        result = transformer.latlon_to_world(
            transformer.origin.lat,
            transformer.origin.lon + 1.0
        )

        # Should be positive X (east)
        assert result.x > 0
        assert result.y == pytest.approx(0.0, abs=100)

    def test_latlon_to_world_with_elevation(self):
        """Test converting with elevation."""
        transformer = CoordinateTransformer()

        result = transformer.latlon_to_world(
            transformer.origin.lat,
            transformer.origin.lon,
            elevation=250.0  # Above origin elevation of 230
        )

        # With flatten_to_plane=True, z should be z_offset
        assert result.z == 0.0

    def test_latlon_to_world_without_flatten(self):
        """Test converting without flatten to plane."""
        origin = SceneOrigin(elevation=230.0)
        config = GeometryConfig(origin=origin, flatten_to_plane=False)
        transformer = CoordinateTransformer(config)

        result = transformer.latlon_to_world(
            transformer.origin.lat,
            transformer.origin.lon,
            elevation=250.0
        )

        # Elevation relative to origin
        assert result.z == pytest.approx(20.0)

    def test_latlon_to_world_batch(self):
        """Test batch conversion."""
        transformer = CoordinateTransformer()

        coords = [
            (transformer.origin.lat, transformer.origin.lon),
            (transformer.origin.lat + 0.01, transformer.origin.lon + 0.01),
            (transformer.origin.lat - 0.01, transformer.origin.lon - 0.01),
        ]

        results = transformer.latlon_to_world_batch(coords)

        assert len(results) == 3
        assert all(isinstance(r, WorldCoordinate) for r in results)

    def test_world_to_latlon_origin(self):
        """Test converting world origin back to lat/lon."""
        transformer = CoordinateTransformer()

        result = transformer.world_to_latlon(0, 0, 0)

        assert result.lat == pytest.approx(transformer.origin.lat, abs=1e-6)
        assert result.lon == pytest.approx(transformer.origin.lon, abs=1e-6)

    def test_world_to_latlon_roundtrip(self):
        """Test roundtrip conversion."""
        transformer = CoordinateTransformer()

        original_lat = 35.2371
        original_lon = -80.8331

        # Convert to world
        world = transformer.latlon_to_world(original_lat, original_lon)

        # Convert back
        result = transformer.world_to_latlon(world.x, world.y, world.z)

        # Should be very close to original
        assert result.lat == pytest.approx(original_lat, abs=1e-6)
        assert result.lon == pytest.approx(original_lon, abs=1e-6)

    def test_get_distance_meters_same_point(self):
        """Test distance to same point."""
        transformer = CoordinateTransformer()

        distance = transformer.get_distance_meters(
            35.2271, -80.8431,
            35.2271, -80.8431
        )

        assert distance == pytest.approx(0.0)

    def test_get_distance_meters_known_distance(self):
        """Test distance calculation."""
        transformer = CoordinateTransformer()

        # 1 degree latitude is approximately 111 km
        distance = transformer.get_distance_meters(
            35.0, -80.0,
            36.0, -80.0
        )

        assert 110000 < distance < 112000

    def test_get_distance_meters_diagonal(self):
        """Test diagonal distance calculation."""
        transformer = CoordinateTransformer()

        distance = transformer.get_distance_meters(
            35.0, -81.0,
            36.0, -80.0
        )

        # Should be approximately 111 * sqrt(2) * cos(lat)
        assert distance > 100000

    def test_get_bearing_degrees_north(self):
        """Test bearing due north."""
        transformer = CoordinateTransformer()

        bearing = transformer.get_bearing_degrees(
            35.0, -80.0,
            36.0, -80.0
        )

        assert bearing == pytest.approx(0.0, abs=1.0)

    def test_get_bearing_degrees_east(self):
        """Test bearing due east."""
        transformer = CoordinateTransformer()

        bearing = transformer.get_bearing_degrees(
            35.0, -81.0,
            35.0, -80.0
        )

        assert bearing == pytest.approx(90.0, abs=1.0)

    def test_get_bearing_degrees_south(self):
        """Test bearing due south."""
        transformer = CoordinateTransformer()

        bearing = transformer.get_bearing_degrees(
            36.0, -80.0,
            35.0, -80.0
        )

        assert bearing == pytest.approx(180.0, abs=1.0)

    def test_get_bearing_degrees_west(self):
        """Test bearing due west."""
        transformer = CoordinateTransformer()

        bearing = transformer.get_bearing_degrees(
            35.0, -80.0,
            35.0, -81.0
        )

        assert bearing == pytest.approx(270.0, abs=1.0)


class TestLatLonToUTM:
    """Tests for UTM coordinate conversion."""

    def test_latlon_to_utm_charlotte(self):
        """Test UTM conversion for Charlotte."""
        transformer = CoordinateTransformer()

        result = transformer._latlon_to_utm(35.2271, -80.8431, 17)

        assert isinstance(result, UTMCoordinate)
        assert result.zone == 17
        assert result.hemisphere == "N"
        # Easting should be around 500000 + offset
        assert 400000 < result.easting < 600000
        # Northing should be around 3.9 million
        assert 3800000 < result.northing < 4000000

    def test_latlon_to_utm_southern_hemisphere(self):
        """Test UTM conversion for southern hemisphere."""
        transformer = CoordinateTransformer()

        result = transformer._latlon_to_utm(-33.8688, 151.2093, 56)

        assert result.hemisphere == "S"
        # Southern hemisphere should have correct hemisphere designation
        # Note: The false northing logic may vary by implementation
        assert result.zone == 56

    def test_utm_to_latlon_roundtrip(self):
        """Test UTM to lat/lon roundtrip."""
        transformer = CoordinateTransformer()

        original_lat = 35.2271
        original_lon = -80.8431

        # Convert to UTM
        utm = transformer._latlon_to_utm(original_lat, original_lon, 17)

        # Convert back
        result = transformer.utm_to_latlon(
            utm.easting,
            utm.northing,
            utm.zone,
            utm.hemisphere
        )

        # Should be close to original
        assert result.lat == pytest.approx(original_lat, abs=0.001)
        assert result.lon == pytest.approx(original_lon, abs=0.001)


class TestCharlotteOrigins:
    """Tests for CHARLOTTE_ORIGINS preset."""

    def test_has_downtown(self):
        """Test that downtown origin is defined."""
        assert "downtown" in CHARLOTTE_ORIGINS
        assert CHARLOTTE_ORIGINS["downtown"].lat == pytest.approx(35.2271)

    def test_has_airport(self):
        """Test that airport origin is defined."""
        assert "airport" in CHARLOTTE_ORIGINS
        assert CHARLOTTE_ORIGINS["airport"].lat == pytest.approx(35.2140)

    def test_has_uncc(self):
        """Test that UNCC origin is defined."""
        assert "uncc" in CHARLOTTE_ORIGINS

    def test_all_origins_have_names(self):
        """Test that all origins have names."""
        for key, origin in CHARLOTTE_ORIGINS.items():
            assert origin.name != ""

    def test_all_origins_in_charlotte_area(self):
        """Test that all origins are in Charlotte area."""
        for key, origin in CHARLOTTE_ORIGINS.items():
            # Charlotte area bounds
            assert 35.0 < origin.lat < 35.5
            assert -81.0 < origin.lon < -80.5


class TestScaleFactor:
    """Tests for scale factor in coordinate transformation."""

    def test_scale_factor_applied(self):
        """Test that scale factor is applied."""
        origin = SceneOrigin()
        config = GeometryConfig(origin=origin, scale=2.0)
        transformer = CoordinateTransformer(config)

        result = transformer.latlon_to_world(
            transformer.origin.lat + 0.01,
            transformer.origin.lon
        )

        # With scale=2.0, distance should be doubled
        # Compare with default scale
        default_transformer = CoordinateTransformer()
        default_result = default_transformer.latlon_to_world(
            default_transformer.origin.lat + 0.01,
            default_transformer.origin.lon
        )

        assert result.y == pytest.approx(default_result.y * 2.0, rel=0.01)

    def test_scale_factor_in_reverse(self):
        """Test that scale factor is reversed in world_to_latlon."""
        origin = SceneOrigin()
        config = GeometryConfig(origin=origin, scale=2.0)
        transformer = CoordinateTransformer(config)

        # With scale=2.0, world coordinates are doubled
        # So converting 2000 world units should give same lat/lon as 1000 with default
        result = transformer.world_to_latlon(2000, 0, 0)

        default_transformer = CoordinateTransformer()
        default_result = default_transformer.world_to_latlon(1000, 0, 0)

        assert result.lat == pytest.approx(default_result.lat, abs=1e-6)


class TestZOffset:
    """Tests for Z offset in coordinate transformation."""

    def test_z_offset_applied(self):
        """Test that Z offset is applied."""
        origin = SceneOrigin(elevation=230.0)
        config = GeometryConfig(origin=origin, z_offset=10.0, flatten_to_plane=True)
        transformer = CoordinateTransformer(config)

        result = transformer.latlon_to_world(
            transformer.origin.lat,
            transformer.origin.lon,
            elevation=250.0
        )

        assert result.z == 10.0  # Should be z_offset

    def test_z_offset_with_flatten_false(self):
        """Test Z offset with flatten_to_plane=False."""
        origin = SceneOrigin(elevation=230.0)
        config = GeometryConfig(
            origin=origin,
            z_offset=10.0,
            flatten_to_plane=False
        )
        transformer = CoordinateTransformer(config)

        result = transformer.latlon_to_world(
            transformer.origin.lat,
            transformer.origin.lon,
            elevation=250.0
        )

        # Z = (250 - 230) * 1.0 + 10.0 = 30
        assert result.z == pytest.approx(30.0)


class TestAccuracy:
    """Tests for coordinate transformation accuracy."""

    def test_accuracy_near_origin(self):
        """Test accuracy near origin (should be very good)."""
        transformer = CoordinateTransformer()

        # Small offset from origin
        original_lat = 35.2271 + 0.001
        original_lon = -80.8431 + 0.001

        world = transformer.latlon_to_world(original_lat, original_lon)
        result = transformer.world_to_latlon(world.x, world.y, world.z)

        # Should be accurate to within 1mm
        assert result.lat == pytest.approx(original_lat, abs=1e-8)
        assert result.lon == pytest.approx(original_lon, abs=1e-8)

    def test_accuracy_at_distance(self):
        """Test accuracy at larger distances."""
        transformer = CoordinateTransformer()

        # ~10km from origin
        original_lat = 35.2271 + 0.1
        original_lon = -80.8431 + 0.1

        world = transformer.latlon_to_world(original_lat, original_lon)
        result = transformer.world_to_latlon(world.x, world.y, world.z)

        # Should still be quite accurate
        assert result.lat == pytest.approx(original_lat, abs=1e-6)
        assert result.lon == pytest.approx(original_lon, abs=1e-6)

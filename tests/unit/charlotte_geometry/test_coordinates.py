"""
Unit tests for lib/charlotte_digital_twin/geometry/coordinates.py

Tests coordinate transformation functionality including:
- WGS84 to UTM conversion
- UTM to local scene coordinates
- CoordinateTransformer class

Note: bpy and mathutils are mocked globally in tests/unit/conftest.py
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import math


class TestCoordinateTransformer:
    """Tests for CoordinateTransformer class."""

    def test_transformer_initialization(self):
        """Test CoordinateTransformer initialization."""
        from lib.charlotte_digital_twin.geometry.coordinates import CoordinateTransformer
        from lib.charlotte_digital_twin.geometry.types import GeometryConfig

        config = GeometryConfig()
        transformer = CoordinateTransformer(config)

        assert transformer.config is not None
        assert transformer.origin is not None

    def test_latlon_to_world_basic(self):
        """Test basic lat/lon to world conversion."""
        from lib.charlotte_digital_twin.geometry.coordinates import CoordinateTransformer
        from lib.charlotte_digital_twin.geometry.types import GeometryConfig

        config = GeometryConfig()
        transformer = CoordinateTransformer(config)

        # Origin point should convert to (0, 0, 0)
        world_pos = transformer.latlon_to_world(
            config.origin.lat,
            config.origin.lon,
        )

        # Should be close to origin (0, 0, 0)
        assert abs(world_pos.x) < 1.0  # Within 1 meter
        assert abs(world_pos.y) < 1.0

    def test_latlon_to_world_offset(self):
        """Test lat/lon conversion with offset from origin."""
        from lib.charlotte_digital_twin.geometry.coordinates import CoordinateTransformer
        from lib.charlotte_digital_twin.geometry.types import GeometryConfig

        config = GeometryConfig()
        transformer = CoordinateTransformer(config)

        # Point 0.01 degrees north should be ~1.11 km north
        world_pos = transformer.latlon_to_world(
            config.origin.lat + 0.01,
            config.origin.lon,
        )

        # Y should be positive (north)
        assert world_pos.y > 1000  # More than 1 km

    def test_scale_factor(self):
        """Test scale factor application."""
        from lib.charlotte_digital_twin.geometry.coordinates import CoordinateTransformer
        from lib.charlotte_digital_twin.geometry.types import GeometryConfig

        # Scale of 0.01 means 1 meter = 0.01 Blender units
        config = GeometryConfig(scale=0.01)
        transformer = CoordinateTransformer(config)

        # Point 100 meters from origin
        world_pos = transformer.latlon_to_world(
            config.origin.lat + 0.001,  # ~111 meters north
            config.origin.lon,
        )

        # With 0.01 scale, should be ~1.11 Blender units
        assert abs(world_pos.y) < 2.0

    def test_latlon_to_world_batch(self):
        """Test batch coordinate conversion."""
        from lib.charlotte_digital_twin.geometry.coordinates import CoordinateTransformer
        from lib.charlotte_digital_twin.geometry.types import GeometryConfig

        config = GeometryConfig()
        transformer = CoordinateTransformer(config)

        # Multiple coordinates
        coords = [
            (config.origin.lat, config.origin.lon),
            (config.origin.lat + 0.01, config.origin.lon),
            (config.origin.lat, config.origin.lon + 0.01),
        ]

        world_coords = transformer.latlon_to_world_batch(coords)

        assert len(world_coords) == 3
        # First should be near origin
        assert abs(world_coords[0].x) < 1.0
        assert abs(world_coords[0].y) < 1.0

    def test_world_to_latlon(self):
        """Test world to lat/lon conversion (round trip)."""
        from lib.charlotte_digital_twin.geometry.coordinates import CoordinateTransformer
        from lib.charlotte_digital_twin.geometry.types import GeometryConfig

        config = GeometryConfig()
        transformer = CoordinateTransformer(config)

        # Convert to world and back
        original_lat = config.origin.lat + 0.005
        original_lon = config.origin.lon + 0.005

        world = transformer.latlon_to_world(original_lat, original_lon)
        geo = transformer.world_to_latlon(world.x, world.y)

        # Should be close to original
        assert abs(geo.lat - original_lat) < 0.0001
        assert abs(geo.lon - original_lon) < 0.0001


class TestUTMConversion:
    """Tests for UTM coordinate conversion."""

    def test_latlon_to_utm_internal(self):
        """Test internal WGS84 to UTM conversion."""
        from lib.charlotte_digital_twin.geometry.coordinates import CoordinateTransformer
        from lib.charlotte_digital_twin.geometry.types import GeometryConfig

        config = GeometryConfig()
        transformer = CoordinateTransformer(config)

        # Charlotte coordinates
        utm = transformer._latlon_to_utm(35.2271, -80.8431, zone=17)

        assert utm is not None
        assert utm.zone == 17
        assert utm.hemisphere == "N"
        # Charlotte UTM coords are around:
        # Easting: ~500000-520000
        # Northing: ~3890000-3910000
        assert 490000 < utm.easting < 530000
        assert 3880000 < utm.northing < 3920000

    def test_utm_to_latlon(self):
        """Test UTM to lat/lon conversion."""
        from lib.charlotte_digital_twin.geometry.coordinates import CoordinateTransformer
        from lib.charlotte_digital_twin.geometry.types import GeometryConfig

        config = GeometryConfig()
        transformer = CoordinateTransformer(config)

        # Charlotte UTM coordinates
        geo = transformer.utm_to_latlon(
            easting=515000.0,
            northing=3900000.0,
            zone=17,
            hemisphere="N",
        )

        assert geo is not None
        # Should be in Charlotte area
        assert 35.0 < geo.lat < 35.5
        assert -81.5 < geo.lon < -80.0


class TestDistanceCalculations:
    """Tests for distance calculation utilities."""

    def test_get_distance_meters(self):
        """Test haversine distance calculation via method."""
        from lib.charlotte_digital_twin.geometry.coordinates import CoordinateTransformer
        from lib.charlotte_digital_twin.geometry.types import GeometryConfig

        config = GeometryConfig()
        transformer = CoordinateTransformer(config)

        # Distance from Charlotte to Raleigh ~240 km
        distance = transformer.get_distance_meters(
            lat1=35.2271,
            lon1=-80.8431,
            lat2=35.7796,
            lon2=-78.6382,
        )

        # Should be approximately 209 km (straight line distance)
        assert 200000 < distance < 220000

    def test_get_distance_same_point(self):
        """Test distance for same point."""
        from lib.charlotte_digital_twin.geometry.coordinates import CoordinateTransformer
        from lib.charlotte_digital_twin.geometry.types import GeometryConfig

        config = GeometryConfig()
        transformer = CoordinateTransformer(config)

        distance = transformer.get_distance_meters(
            lat1=35.0,
            lon1=-80.0,
            lat2=35.0,
            lon2=-80.0,
        )

        assert distance == pytest.approx(0.0, abs=1.0)

    def test_get_bearing_degrees(self):
        """Test bearing calculation."""
        from lib.charlotte_digital_twin.geometry.coordinates import CoordinateTransformer
        from lib.charlotte_digital_twin.geometry.types import GeometryConfig

        config = GeometryConfig()
        transformer = CoordinateTransformer(config)

        # Bearing due north
        bearing = transformer.get_bearing_degrees(
            lat1=35.0,
            lon1=-80.0,
            lat2=36.0,
            lon2=-80.0,
        )

        # Should be close to 0 (north)
        assert 0 <= bearing <= 10 or 350 <= bearing <= 360


class TestCharlotteOrigins:
    """Tests for Charlotte origin presets."""

    def test_downtown_origin(self):
        """Test downtown Charlotte origin preset."""
        from lib.charlotte_digital_twin.geometry.coordinates import CHARLOTTE_ORIGINS

        downtown = CHARLOTTE_ORIGINS["downtown"]

        assert downtown.lat == pytest.approx(35.2271, rel=0.001)
        assert downtown.lon == pytest.approx(-80.8431, rel=0.001)
        assert downtown.name == "Charlotte Downtown"

    def test_all_origins_exist(self):
        """Test all expected origins exist."""
        from lib.charlotte_digital_twin.geometry.coordinates import CHARLOTTE_ORIGINS

        expected = ["downtown", "airport", "uncc", "southpark", "noda"]
        for key in expected:
            assert key in CHARLOTTE_ORIGINS
            assert CHARLOTTE_ORIGINS[key].lat != 0
            assert CHARLOTTE_ORIGINS[key].lon != 0

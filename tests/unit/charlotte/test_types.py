"""
Unit tests for Charlotte Digital Twin geometry types module.

Tests type definitions, serialization, and pure functions without Blender.

Note: bpy and mathutils are mocked in conftest.py before any imports.
"""

import pytest
from dataclasses import asdict

from lib.charlotte_digital_twin.geometry.types import (
    # Enums
    DetailLevel,
    RoadType,
    BuildingType,
    POICategory,
    # Data classes
    SceneOrigin,
    GeometryConfig,
    WorldCoordinate,
    GeoCoordinate,
    UTMCoordinate,
    RoadSegment,
    BuildingFootprint,
    POIMarker,
    SceneBounds,
    # Constants
    ROAD_WIDTHS,
    ROAD_LANES,
)


class TestDetailLevel:
    """Tests for DetailLevel enum."""

    def test_level_values(self):
        """Test detail level values."""
        assert DetailLevel.MINIMAL.value == "minimal"
        assert DetailLevel.STANDARD.value == "standard"
        assert DetailLevel.HIGH.value == "high"
        assert DetailLevel.ULTRA.value == "ultra"

    def test_level_ordering(self):
        """Test detail levels can be compared."""
        levels = [
            DetailLevel.MINIMAL,
            DetailLevel.STANDARD,
            DetailLevel.HIGH,
            DetailLevel.ULTRA
        ]
        # All should be valid enum members
        assert len(levels) == 4


class TestRoadType:
    """Tests for RoadType enum."""

    def test_highway_types(self):
        """Test highway road types."""
        assert RoadType.MOTORWAY.value == "motorway"
        assert RoadType.MOTORWAY_LINK.value == "motorway_link"
        assert RoadType.TRUNK.value == "trunk"

    def test_urban_types(self):
        """Test urban road types."""
        assert RoadType.PRIMARY.value == "primary"
        assert RoadType.SECONDARY.value == "secondary"
        assert RoadType.TERTIARY.value == "tertiary"
        assert RoadType.RESIDENTIAL.value == "residential"

    def test_pedestrian_types(self):
        """Test pedestrian road types."""
        assert RoadType.FOOTWAY.value == "footway"
        assert RoadType.PEDESTRIAN.value == "pedestrian"
        assert RoadType.CYCLEWAY.value == "cycleway"


class TestBuildingType:
    """Tests for BuildingType enum."""

    def test_common_types(self):
        """Test common building types."""
        assert BuildingType.OFFICE.value == "office"
        assert BuildingType.RESIDENTIAL.value == "residential"
        assert BuildingType.COMMERCIAL.value == "commercial"

    def test_special_types(self):
        """Test special building types."""
        assert BuildingType.HOSPITAL.value == "hospital"
        assert BuildingType.STADIUM.value == "stadium"
        assert BuildingType.TRAIN_STATION.value == "train_station"


class TestPOICategory:
    """Tests for POICategory enum."""

    def test_common_categories(self):
        """Test common POI categories."""
        assert POICategory.RESTAURANT.value == "RESTAURANT"
        assert POICategory.CAFE.value == "CAFE"
        assert POICategory.HOTEL.value == "HOTEL"

    def test_public_categories(self):
        """Test public service categories."""
        assert POICategory.POLICE.value == "POLICE"
        assert POICategory.HOSPITAL.value == "HOSPITAL"
        assert POICategory.LIBRARY.value == "LIBRARY"


class TestSceneOrigin:
    """Tests for SceneOrigin dataclass."""

    def test_default_values(self):
        """Test default Charlotte downtown values."""
        origin = SceneOrigin()

        assert origin.lat == pytest.approx(35.2271)
        assert origin.lon == pytest.approx(-80.8431)
        assert origin.name == "Charlotte Downtown"
        assert origin.elevation == 230.0
        assert origin.utm_zone == 17
        assert origin.utm_hemisphere == "N"

    def test_custom_values(self):
        """Test custom origin values."""
        origin = SceneOrigin(
            lat=40.7128,
            lon=-74.0060,
            name="NYC",
            elevation=10.0,
            utm_zone=18
        )

        assert origin.lat == pytest.approx(40.7128)
        assert origin.name == "NYC"


class TestGeometryConfig:
    """Tests for GeometryConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = GeometryConfig()

        assert config.scale == 1.0
        assert config.detail_level == DetailLevel.STANDARD
        assert config.flatten_to_plane is True
        assert config.default_road_width == 7.0
        assert config.default_building_height == 10.0

    def test_to_dict(self):
        """Test serialization to dictionary."""
        config = GeometryConfig()
        data = config.to_dict()

        assert "origin" in data
        assert "scale" in data
        assert data["scale"] == 1.0
        assert data["detail_level"] == "standard"

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {
            "scale": 2.0,
            "detail_level": "high",
            "default_road_width": 10.0,
            "origin": {
                "lat": 35.0,
                "lon": -81.0,
                "name": "Test",
                "elevation": 200.0,
                "utm_zone": 17,
                "utm_hemisphere": "N"
            }
        }

        config = GeometryConfig.from_dict(data)

        assert config.scale == 2.0
        assert config.detail_level == DetailLevel.HIGH
        assert config.default_road_width == 10.0

    def test_roundtrip_serialization(self):
        """Test that to_dict/from_dict is lossless."""
        original = GeometryConfig(
            scale=0.5,
            detail_level=DetailLevel.ULTRA,
            flatten_to_plane=False,
            z_offset=5.0
        )

        data = original.to_dict()
        restored = GeometryConfig.from_dict(data)

        assert restored.scale == original.scale
        assert restored.detail_level == original.detail_level
        assert restored.flatten_to_plane == original.flatten_to_plane


class TestWorldCoordinate:
    """Tests for WorldCoordinate dataclass."""

    def test_default_values(self):
        """Test default values."""
        coord = WorldCoordinate(x=0, y=0, z=0)

        assert coord.x == 0.0
        assert coord.y == 0.0
        assert coord.z == 0.0

    def test_custom_values(self):
        """Test custom values."""
        coord = WorldCoordinate(x=100.5, y=-50.25, z=10.0)

        assert coord.x == 100.5
        assert coord.y == -50.25
        assert coord.z == 10.0

    def test_to_tuple(self):
        """Test conversion to tuple."""
        coord = WorldCoordinate(x=1, y=2, z=3)
        result = coord.to_tuple()

        assert result == (1.0, 2.0, 3.0)
        assert isinstance(result, tuple)

    def test_to_list(self):
        """Test conversion to list."""
        coord = WorldCoordinate(x=1, y=2, z=3)
        result = coord.to_list()

        assert result == [1.0, 2.0, 3.0]
        assert isinstance(result, list)


class TestGeoCoordinate:
    """Tests for GeoCoordinate dataclass."""

    def test_default_values(self):
        """Test default values."""
        coord = GeoCoordinate(lat=0, lon=0)

        assert coord.lat == 0.0
        assert coord.lon == 0.0
        assert coord.elevation == 0.0

    def test_with_elevation(self):
        """Test with elevation."""
        coord = GeoCoordinate(lat=35.2271, lon=-80.8431, elevation=230.0)

        assert coord.elevation == 230.0


class TestUTMCoordinate:
    """Tests for UTMCoordinate dataclass."""

    def test_values(self):
        """Test UTM coordinate values."""
        coord = UTMCoordinate(
            easting=500000.0,
            northing=3900000.0,
            zone=17,
            hemisphere="N"
        )

        assert coord.easting == 500000.0
        assert coord.northing == 3900000.0
        assert coord.zone == 17
        assert coord.hemisphere == "N"


class TestRoadSegment:
    """Tests for RoadSegment dataclass."""

    def test_get_length_straight(self):
        """Test length calculation for straight segment."""
        segment = RoadSegment(
            osm_id=1,
            name="Test Road",
            road_type=RoadType.PRIMARY,
            coordinates=[
                WorldCoordinate(x=0, y=0, z=0),
                WorldCoordinate(x=100, y=0, z=0),
                WorldCoordinate(x=200, y=0, z=0),
            ],
            width=10.0,
            lanes=2,
            surface="asphalt",
            is_bridge=False,
            is_tunnel=False,
            is_oneway=False
        )

        length = segment.get_length()

        assert length == pytest.approx(200.0)

    def test_get_length_diagonal(self):
        """Test length calculation for diagonal segment."""
        segment = RoadSegment(
            osm_id=1,
            name="Diagonal Road",
            road_type=RoadType.PRIMARY,
            coordinates=[
                WorldCoordinate(x=0, y=0, z=0),
                WorldCoordinate(x=100, y=100, z=0),
            ],
            width=10.0,
            lanes=2,
            surface="asphalt",
            is_bridge=False,
            is_tunnel=False,
            is_oneway=False
        )

        length = segment.get_length()

        # Diagonal of 100x100 square
        expected = (100**2 + 100**2) ** 0.5
        assert length == pytest.approx(expected)

    def test_default_values(self):
        """Test default values."""
        segment = RoadSegment(
            osm_id=1,
            name="Test",
            road_type=RoadType.RESIDENTIAL,
            coordinates=[WorldCoordinate(x=0, y=0, z=0)],
            width=7.0,
            lanes=2,
            surface="asphalt",
            is_bridge=False,
            is_tunnel=False,
            is_oneway=False
        )

        assert segment.tags == {}


class TestBuildingFootprint:
    """Tests for BuildingFootprint dataclass."""

    def test_get_center(self):
        """Test center calculation."""
        footprint = BuildingFootprint(
            osm_id=1,
            name="Test Building",
            building_type=BuildingType.OFFICE,
            coordinates=[
                WorldCoordinate(x=0, y=0, z=0),
                WorldCoordinate(x=20, y=0, z=0),
                WorldCoordinate(x=20, y=20, z=0),
                WorldCoordinate(x=0, y=20, z=0),
            ],
            height=50.0,
            levels=10,
            outline=[]
        )

        center = footprint.get_center()

        assert center.x == pytest.approx(10.0)
        assert center.y == pytest.approx(10.0)

    def test_get_center_empty(self):
        """Test center calculation with empty coordinates."""
        footprint = BuildingFootprint(
            osm_id=1,
            name="Empty",
            building_type=BuildingType.YES,
            coordinates=[],
            height=10.0,
            levels=None,
            outline=[]
        )

        center = footprint.get_center()

        assert center.x == 0
        assert center.y == 0

    def test_get_area_square(self):
        """Test area calculation for square footprint."""
        footprint = BuildingFootprint(
            osm_id=1,
            name="Square",
            building_type=BuildingType.OFFICE,
            coordinates=[
                WorldCoordinate(x=0, y=0, z=0),
                WorldCoordinate(x=10, y=0, z=0),
                WorldCoordinate(x=10, y=10, z=0),
                WorldCoordinate(x=0, y=10, z=0),
            ],
            height=30.0,
            levels=5,
            outline=[]
        )

        area = footprint.get_area()

        assert area == pytest.approx(100.0)

    def test_get_area_rectangle(self):
        """Test area calculation for rectangular footprint."""
        footprint = BuildingFootprint(
            osm_id=1,
            name="Rectangle",
            building_type=BuildingType.OFFICE,
            coordinates=[
                WorldCoordinate(x=0, y=0, z=0),
                WorldCoordinate(x=20, y=0, z=0),
                WorldCoordinate(x=20, y=10, z=0),
                WorldCoordinate(x=0, y=10, z=0),
            ],
            height=30.0,
            levels=5,
            outline=[]
        )

        area = footprint.get_area()

        assert area == pytest.approx(200.0)

    def test_get_area_insufficient_points(self):
        """Test area calculation with fewer than 3 points."""
        footprint = BuildingFootprint(
            osm_id=1,
            name="Line",
            building_type=BuildingType.YES,
            coordinates=[
                WorldCoordinate(x=0, y=0, z=0),
                WorldCoordinate(x=10, y=0, z=0),
            ],
            height=10.0,
            levels=None,
            outline=[]
        )

        area = footprint.get_area()

        assert area == 0.0


class TestPOIMarker:
    """Tests for POIMarker dataclass."""

    def test_default_values(self):
        """Test default values."""
        marker = POIMarker(
            osm_id=1,
            name="Test POI",
            category=POICategory.RESTAURANT,
            position=WorldCoordinate(x=0, y=0, z=0)
        )

        assert marker.importance == 0.5
        assert marker.tags == {}

    def test_custom_importance(self):
        """Test custom importance value."""
        marker = POIMarker(
            osm_id=1,
            name="Important POI",
            category=POICategory.HOSPITAL,
            position=WorldCoordinate(x=100, y=100, z=0),
            importance=0.9
        )

        assert marker.importance == 0.9


class TestSceneBounds:
    """Tests for SceneBounds dataclass."""

    def test_contains_point_inside(self):
        """Test contains with point inside bounds."""
        bounds = SceneBounds(
            min_lat=35.0,
            max_lat=36.0,
            min_lon=-81.0,
            max_lon=-80.0
        )

        assert bounds.contains(35.5, -80.5) is True

    def test_contains_point_outside(self):
        """Test contains with point outside bounds."""
        bounds = SceneBounds(
            min_lat=35.0,
            max_lat=36.0,
            min_lon=-81.0,
            max_lon=-80.0
        )

        assert bounds.contains(34.0, -80.5) is False
        assert bounds.contains(35.5, -82.0) is False

    def test_contains_point_on_edge(self):
        """Test contains with point on edge."""
        bounds = SceneBounds(
            min_lat=35.0,
            max_lat=36.0,
            min_lon=-81.0,
            max_lon=-80.0
        )

        assert bounds.contains(35.0, -80.5) is True
        assert bounds.contains(36.0, -80.5) is True

    def test_from_center_radius(self):
        """Test creating bounds from center and radius."""
        bounds = SceneBounds.from_center_radius(35.2271, -80.8431, 2.0)

        # Should be approximately 2km in each direction
        delta = 2.0 / 111.0
        assert bounds.max_lat == pytest.approx(35.2271 + delta, rel=0.01)
        assert bounds.min_lat == pytest.approx(35.2271 - delta, rel=0.01)

    def test_charlotte_downtown(self):
        """Test Charlotte downtown preset."""
        bounds = SceneBounds.charlotte_downtown(radius_km=1.0)

        assert 35.0 < bounds.min_lat < bounds.max_lat < 36.0
        assert -81.0 < bounds.min_lon < bounds.max_lon < -80.0

    def test_charlotte_metro(self):
        """Test Charlotte metro preset."""
        bounds = SceneBounds.charlotte_metro()

        assert bounds.min_lat == 35.0
        assert bounds.max_lat == 35.4
        assert bounds.min_lon == -80.9
        assert bounds.max_lon == -80.5

    def test_to_dict(self):
        """Test serialization to dictionary."""
        bounds = SceneBounds(
            min_lat=35.0,
            max_lat=36.0,
            min_lon=-81.0,
            max_lon=-80.0
        )

        data = bounds.to_dict()

        assert data["min_lat"] == 35.0
        assert data["max_lat"] == 36.0


class TestRoadWidths:
    """Tests for ROAD_WIDTHS constant."""

    def test_motorway_width(self):
        """Test motorway width."""
        assert ROAD_WIDTHS[RoadType.MOTORWAY] == 25.0

    def test_residential_width(self):
        """Test residential width."""
        assert ROAD_WIDTHS[RoadType.RESIDENTIAL] == 7.0

    def test_all_road_types_have_widths(self):
        """Test that all road types have width values."""
        for road_type in RoadType:
            assert road_type in ROAD_WIDTHS
            assert ROAD_WIDTHS[road_type] > 0


class TestRoadLanes:
    """Tests for ROAD_LANES constant."""

    def test_motorway_lanes(self):
        """Test motorway lane count."""
        assert ROAD_LANES[RoadType.MOTORWAY] == 4

    def test_residential_lanes(self):
        """Test residential lane count."""
        assert ROAD_LANES[RoadType.RESIDENTIAL] == 2

    def test_all_road_types_have_lanes(self):
        """Test that all road types have lane values."""
        for road_type in RoadType:
            assert road_type in ROAD_LANES
            assert ROAD_LANES[road_type] >= 1

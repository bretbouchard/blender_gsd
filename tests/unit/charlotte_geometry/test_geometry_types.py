"""
Unit tests for lib/charlotte_digital_twin/geometry/types.py

Tests core geometry types including:
- SceneOrigin and GeometryConfig
- Coordinate types (WorldCoordinate, GeoCoordinate, UTMCoordinate)
- RoadSegment, BuildingFootprint, POIMarker
- SceneBounds and utility methods
- Enum types (DetailLevel, RoadType, BuildingType, POICategory)
"""

import pytest
from dataclasses import asdict
from pathlib import Path


class TestSceneOrigin:
    """Tests for SceneOrigin dataclass."""

    def test_default_scene_origin(self):
        """Test default SceneOrigin (Charlotte Downtown)."""
        from lib.charlotte_digital_twin.geometry.types import SceneOrigin

        origin = SceneOrigin()

        assert origin.lat == 35.2271
        assert origin.lon == -80.8431
        assert origin.name == "Charlotte Downtown"
        assert origin.elevation == 230.0
        assert origin.utm_zone == 17
        assert origin.utm_hemisphere == "N"

    def test_custom_scene_origin(self):
        """Test SceneOrigin with custom values."""
        from lib.charlotte_digital_twin.geometry.types import SceneOrigin

        origin = SceneOrigin(
            lat=40.7128,
            lon=-74.0060,
            name="New York City",
            elevation=10.0,
            utm_zone=18,
        )

        assert origin.lat == 40.7128
        assert origin.lon == -74.0060
        assert origin.name == "New York City"
        assert origin.elevation == 10.0
        assert origin.utm_zone == 18


class TestGeometryConfig:
    """Tests for GeometryConfig dataclass."""

    def test_default_geometry_config(self):
        """Test default GeometryConfig values."""
        from lib.charlotte_digital_twin.geometry.types import (
            GeometryConfig,
            DetailLevel,
        )

        config = GeometryConfig()

        assert config.scale == 1.0
        assert config.detail_level == DetailLevel.STANDARD
        assert config.flatten_to_plane is True
        assert config.default_road_width == 7.0
        assert config.default_building_height == 10.0
        assert config.max_building_height == 500.0
        assert config.min_building_height == 3.0

    def test_geometry_config_to_dict(self):
        """Test GeometryConfig serialization."""
        from lib.charlotte_digital_twin.geometry.types import GeometryConfig

        config = GeometryConfig()
        data = config.to_dict()

        assert "origin" in data
        assert data["scale"] == 1.0
        assert data["detail_level"] == "standard"
        assert data["default_road_width"] == 7.0

    def test_geometry_config_from_dict(self):
        """Test GeometryConfig deserialization."""
        from lib.charlotte_digital_twin.geometry.types import (
            GeometryConfig,
            DetailLevel,
        )

        data = {
            "scale": 2.0,
            "detail_level": "high",
            "default_road_width": 10.0,
        }

        config = GeometryConfig.from_dict(data)

        assert config.scale == 2.0
        assert config.detail_level == DetailLevel.HIGH
        assert config.default_road_width == 10.0


class TestDetailLevel:
    """Tests for DetailLevel enum."""

    def test_detail_levels(self):
        """Test all DetailLevel enum values."""
        from lib.charlotte_digital_twin.geometry.types import DetailLevel

        assert DetailLevel.MINIMAL.value == "minimal"
        assert DetailLevel.STANDARD.value == "standard"
        assert DetailLevel.HIGH.value == "high"
        assert DetailLevel.ULTRA.value == "ultra"


class TestRoadType:
    """Tests for RoadType enum."""

    def test_road_types(self):
        """Test key RoadType enum values."""
        from lib.charlotte_digital_twin.geometry.types import RoadType

        assert RoadType.MOTORWAY.value == "motorway"
        assert RoadType.PRIMARY.value == "primary"
        assert RoadType.SECONDARY.value == "secondary"
        assert RoadType.RESIDENTIAL.value == "residential"
        assert RoadType.FOOTWAY.value == "footway"


class TestBuildingType:
    """Tests for BuildingType enum."""

    def test_building_types(self):
        """Test key BuildingType enum values."""
        from lib.charlotte_digital_twin.geometry.types import BuildingType

        assert BuildingType.YES.value == "yes"
        assert BuildingType.APARTMENTS.value == "apartments"
        assert BuildingType.COMMERCIAL.value == "commercial"
        assert BuildingType.OFFICE.value == "office"


class TestPOICategory:
    """Tests for POICategory enum."""

    def test_poi_categories(self):
        """Test key POICategory enum values."""
        from lib.charlotte_digital_twin.geometry.types import POICategory

        assert POICategory.RESTAURANT.value == "RESTAURANT"
        assert POICategory.CAFE.value == "CAFE"
        assert POICategory.HOTEL.value == "HOTEL"
        assert POICategory.ATTRACTION.value == "ATTRACTION"


class TestWorldCoordinate:
    """Tests for WorldCoordinate dataclass."""

    def test_world_coordinate(self):
        """Test WorldCoordinate creation and methods."""
        from lib.charlotte_digital_twin.geometry.types import WorldCoordinate

        coord = WorldCoordinate(x=100.0, y=200.0, z=10.0)

        assert coord.x == 100.0
        assert coord.y == 200.0
        assert coord.z == 10.0

        assert coord.to_tuple() == (100.0, 200.0, 10.0)
        assert coord.to_list() == [100.0, 200.0, 10.0]


class TestGeoCoordinate:
    """Tests for GeoCoordinate dataclass."""

    def test_geo_coordinate(self):
        """Test GeoCoordinate creation."""
        from lib.charlotte_digital_twin.geometry.types import GeoCoordinate

        coord = GeoCoordinate(lat=35.2271, lon=-80.8431, elevation=230.0)

        assert coord.lat == 35.2271
        assert coord.lon == -80.8431
        assert coord.elevation == 230.0

    def test_geo_coordinate_default_elevation(self):
        """Test GeoCoordinate with default elevation."""
        from lib.charlotte_digital_twin.geometry.types import GeoCoordinate

        coord = GeoCoordinate(lat=35.0, lon=-80.0)

        assert coord.elevation == 0.0


class TestUTMCoordinate:
    """Tests for UTMCoordinate dataclass."""

    def test_utm_coordinate(self):
        """Test UTMCoordinate creation."""
        from lib.charlotte_digital_twin.geometry.types import UTMCoordinate

        coord = UTMCoordinate(
            easting=500000.0,
            northing=3900000.0,
            zone=17,
            hemisphere="N",
        )

        assert coord.easting == 500000.0
        assert coord.northing == 3900000.0
        assert coord.zone == 17
        assert coord.hemisphere == "N"


class TestRoadSegment:
    """Tests for RoadSegment dataclass."""

    def test_road_segment(self):
        """Test RoadSegment creation."""
        from lib.charlotte_digital_twin.geometry.types import (
            RoadSegment,
            RoadType,
            WorldCoordinate,
        )

        segment = RoadSegment(
            osm_id=12345,
            name="Main Street",
            road_type=RoadType.PRIMARY,
            coordinates=[
                WorldCoordinate(0, 0, 0),
                WorldCoordinate(100, 0, 0),
                WorldCoordinate(200, 0, 0),
            ],
            width=12.0,
            lanes=2,
            surface="asphalt",
            is_bridge=False,
            is_tunnel=False,
            is_oneway=False,
        )

        assert segment.osm_id == 12345
        assert segment.name == "Main Street"
        assert segment.road_type == RoadType.PRIMARY
        assert len(segment.coordinates) == 3
        assert segment.width == 12.0

    def test_road_segment_length(self):
        """Test RoadSegment get_length calculation."""
        from lib.charlotte_digital_twin.geometry.types import (
            RoadSegment,
            RoadType,
            WorldCoordinate,
        )

        segment = RoadSegment(
            osm_id=1,
            name="Test Road",
            road_type=RoadType.RESIDENTIAL,
            coordinates=[
                WorldCoordinate(0, 0, 0),
                WorldCoordinate(100, 0, 0),
            ],
            width=7.0,
            lanes=2,
            surface="asphalt",
            is_bridge=False,
            is_tunnel=False,
            is_oneway=False,
        )

        length = segment.get_length()
        assert length == pytest.approx(100.0, rel=0.01)


class TestBuildingFootprint:
    """Tests for BuildingFootprint dataclass."""

    def test_building_footprint(self):
        """Test BuildingFootprint creation."""
        from lib.charlotte_digital_twin.geometry.types import (
            BuildingFootprint,
            BuildingType,
            WorldCoordinate,
        )

        footprint = BuildingFootprint(
            osm_id=54321,
            name="Office Building",
            building_type=BuildingType.OFFICE,
            coordinates=[
                WorldCoordinate(0, 0, 0),
                WorldCoordinate(20, 0, 0),
                WorldCoordinate(20, 30, 0),
                WorldCoordinate(0, 30, 0),
            ],
            height=50.0,
            levels=15,
            outline=[
                WorldCoordinate(0, 0, 0),
                WorldCoordinate(20, 0, 0),
                WorldCoordinate(20, 30, 0),
                WorldCoordinate(0, 30, 0),
            ],
        )

        assert footprint.osm_id == 54321
        assert footprint.building_type == BuildingType.OFFICE
        assert footprint.height == 50.0
        assert footprint.levels == 15

    def test_building_footprint_center(self):
        """Test BuildingFootprint get_center calculation."""
        from lib.charlotte_digital_twin.geometry.types import (
            BuildingFootprint,
            BuildingType,
            WorldCoordinate,
        )

        footprint = BuildingFootprint(
            osm_id=1,
            name="Test",
            building_type=BuildingType.YES,
            coordinates=[
                WorldCoordinate(0, 0, 0),
                WorldCoordinate(10, 0, 0),
                WorldCoordinate(10, 10, 0),
                WorldCoordinate(0, 10, 0),
            ],
            height=10.0,
            levels=None,
            outline=[],
        )

        center = footprint.get_center()
        assert center.x == 5.0
        assert center.y == 5.0

    def test_building_footprint_area(self):
        """Test BuildingFootprint get_area calculation (shoelace formula)."""
        from lib.charlotte_digital_twin.geometry.types import (
            BuildingFootprint,
            BuildingType,
            WorldCoordinate,
        )

        # 10x10 square = 100 sq meters
        footprint = BuildingFootprint(
            osm_id=1,
            name="Test",
            building_type=BuildingType.YES,
            coordinates=[
                WorldCoordinate(0, 0, 0),
                WorldCoordinate(10, 0, 0),
                WorldCoordinate(10, 10, 0),
                WorldCoordinate(0, 10, 0),
            ],
            height=10.0,
            levels=None,
            outline=[],
        )

        area = footprint.get_area()
        assert area == pytest.approx(100.0, rel=0.01)


class TestPOIMarker:
    """Tests for POIMarker dataclass."""

    def test_poi_marker(self):
        """Test POIMarker creation."""
        from lib.charlotte_digital_twin.geometry.types import (
            POIMarker,
            POICategory,
            WorldCoordinate,
        )

        marker = POIMarker(
            osm_id=99999,
            name="Coffee Shop",
            category=POICategory.CAFE,
            position=WorldCoordinate(100, 200, 0),
            importance=0.8,
        )

        assert marker.osm_id == 99999
        assert marker.name == "Coffee Shop"
        assert marker.category == POICategory.CAFE
        assert marker.importance == 0.8


class TestSceneBounds:
    """Tests for SceneBounds dataclass."""

    def test_scene_bounds(self):
        """Test SceneBounds creation."""
        from lib.charlotte_digital_twin.geometry.types import SceneBounds

        bounds = SceneBounds(
            min_lat=35.0,
            max_lat=35.5,
            min_lon=-81.0,
            max_lon=-80.5,
        )

        assert bounds.min_lat == 35.0
        assert bounds.max_lat == 35.5
        assert bounds.min_lon == -81.0
        assert bounds.max_lon == -80.5

    def test_scene_bounds_from_center_radius(self):
        """Test SceneBounds.from_center_radius calculation."""
        from lib.charlotte_digital_twin.geometry.types import SceneBounds

        bounds = SceneBounds.from_center_radius(
            center_lat=35.0,
            center_lon=-80.0,
            radius_km=1.0,
        )

        # 1 km ≈ 0.009 degrees
        delta = 1.0 / 111.0
        assert bounds.min_lat == pytest.approx(35.0 - delta, rel=0.001)
        assert bounds.max_lat == pytest.approx(35.0 + delta, rel=0.001)

    def test_scene_bounds_charlotte_downtown(self):
        """Test SceneBounds.charlotte_downtown factory method."""
        from lib.charlotte_digital_twin.geometry.types import SceneBounds

        bounds = SceneBounds.charlotte_downtown(radius_km=2.0)

        # Center should be Charlotte downtown
        center_lat = (bounds.min_lat + bounds.max_lat) / 2
        center_lon = (bounds.min_lon + bounds.max_lon) / 2

        assert center_lat == pytest.approx(35.2271, rel=0.001)
        assert center_lon == pytest.approx(-80.8431, rel=0.001)

    def test_scene_bounds_contains(self):
        """Test SceneBounds.contains method."""
        from lib.charlotte_digital_twin.geometry.types import SceneBounds

        bounds = SceneBounds(
            min_lat=35.0,
            max_lat=36.0,
            min_lon=-81.0,
            max_lon=-80.0,
        )

        assert bounds.contains(35.5, -80.5) is True
        assert bounds.contains(34.5, -80.5) is False
        assert bounds.contains(35.5, -82.0) is False

    def test_scene_bounds_to_dict(self):
        """Test SceneBounds serialization."""
        from lib.charlotte_digital_twin.geometry.types import SceneBounds

        bounds = SceneBounds(
            min_lat=35.0,
            max_lat=36.0,
            min_lon=-81.0,
            max_lon=-80.0,
        )

        data = bounds.to_dict()

        assert data["min_lat"] == 35.0
        assert data["max_lat"] == 36.0
        assert data["min_lon"] == -81.0
        assert data["max_lon"] == -80.0


class TestRoadWidths:
    """Tests for ROAD_WIDTHS constant."""

    def test_road_widths_exist(self):
        """Test that ROAD_WIDTHS has entries for all road types."""
        from lib.charlotte_digital_twin.geometry.types import (
            ROAD_WIDTHS,
            RoadType,
        )

        # Check key road types have width entries
        assert RoadType.MOTORWAY in ROAD_WIDTHS
        assert RoadType.PRIMARY in ROAD_WIDTHS
        assert RoadType.RESIDENTIAL in ROAD_WIDTHS

        # Motorway should be wider than residential
        assert ROAD_WIDTHS[RoadType.MOTORWAY] > ROAD_WIDTHS[RoadType.RESIDENTIAL]


class TestRoadLanes:
    """Tests for ROAD_LANES constant."""

    def test_road_lanes_exist(self):
        """Test that ROAD_LANES has entries for all road types."""
        from lib.charlotte_digital_twin.geometry.types import (
            ROAD_LANES,
            RoadType,
        )

        # Check key road types have lane entries
        assert RoadType.MOTORWAY in ROAD_LANES
        assert RoadType.PRIMARY in ROAD_LANES
        assert RoadType.RESIDENTIAL in ROAD_LANES

        # Motorway should have more lanes than residential
        assert ROAD_LANES[RoadType.MOTORWAY] >= ROAD_LANES[RoadType.RESIDENTIAL]

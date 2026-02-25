"""
Charlotte Digital Twin Geometry Pipeline Integration Tests

Tests end-to-end geometry generation workflows:
- Coordinate transformation pipeline
- Road network generation
- Building extrusion
- Scene assembly

Note: These tests work without Blender using mocked bpy.
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from lib.oracle import compare_numbers, compare_vectors, Oracle


@pytest.mark.integration
class TestCoordinatePipeline:
    """Tests for coordinate transformation pipeline."""

    def test_wgs84_to_world_pipeline(self):
        """WGS84 coordinates should transform through the full pipeline."""
        from lib.charlotte_digital_twin.geometry.coordinates import (
            CoordinateTransformer,
        )
        from lib.charlotte_digital_twin.geometry.types import GeometryConfig

        config = GeometryConfig()
        transformer = CoordinateTransformer(config)

        # Charlotte downtown coordinates
        lat, lon = 35.2271, -80.8431

        # Transform to world
        world = transformer.latlon_to_world(lat, lon)

        # Should be near origin (since these are the default origin coords)
        compare_numbers(abs(world.x), 0.0, tolerance=1.0)
        compare_numbers(abs(world.y), 0.0, tolerance=1.0)

    def test_batch_coordinate_transform(self):
        """Batch coordinate transformation should be consistent."""
        from lib.charlotte_digital_twin.geometry.coordinates import (
            CoordinateTransformer,
        )
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

        # First should be at origin
        compare_numbers(abs(world_coords[0].x), 0.0, tolerance=1.0)
        compare_numbers(abs(world_coords[0].y), 0.0, tolerance=1.0)

        # Second should be north (positive Y)
        assert world_coords[1].y > world_coords[0].y

    def test_roundtrip_transformation(self):
        """Coordinates should roundtrip with minimal error."""
        from lib.charlotte_digital_twin.geometry.coordinates import (
            CoordinateTransformer,
        )
        from lib.charlotte_digital_twin.geometry.types import GeometryConfig

        config = GeometryConfig()
        transformer = CoordinateTransformer(config)

        original_lat = config.origin.lat + 0.005
        original_lon = config.origin.lon + 0.005

        # Forward transform
        world = transformer.latlon_to_world(original_lat, original_lon)

        # Reverse transform
        geo = transformer.world_to_latlon(world.x, world.y)

        # Should be close to original
        compare_numbers(geo.lat, original_lat, tolerance=0.0001)
        compare_numbers(geo.lon, original_lon, tolerance=0.0001)


@pytest.mark.integration
class TestRoadNetworkPipeline:
    """Tests for road network generation pipeline."""

    def test_road_segment_creation(self):
        """Road segments should be created from coordinate data."""
        from lib.charlotte_digital_twin.geometry.types import (
            RoadSegment,
            RoadType,
            WorldCoordinate,
        )

        road = RoadSegment(
            osm_id=12345,
            name="Test Highway",
            road_type=RoadType.MOTORWAY,
            coordinates=[
                WorldCoordinate(x=0, y=0, z=0),
                WorldCoordinate(x=100, y=0, z=0),
                WorldCoordinate(x=200, y=10, z=0),
            ],
            width=25.0,
            lanes=4,
            surface="asphalt",
            is_bridge=False,
            is_tunnel=False,
            is_oneway=False,
        )

        assert road.road_type == RoadType.MOTORWAY
        compare_numbers(road.width, 25.0)
        assert len(road.coordinates) == 3

    def test_road_type_width_mapping(self):
        """Road types should map to appropriate widths."""
        from lib.charlotte_digital_twin.geometry.types import (
            RoadType,
            ROAD_WIDTHS,
        )

        # Motorway should be wider than residential
        assert ROAD_WIDTHS.get(RoadType.MOTORWAY, 0) > ROAD_WIDTHS.get(
            RoadType.RESIDENTIAL, 0
        )


@pytest.mark.integration
class TestBuildingPipeline:
    """Tests for building extrusion pipeline."""

    def test_building_footprint_creation(self):
        """Building footprints should be created from coordinate data."""
        from lib.charlotte_digital_twin.geometry.types import (
            BuildingFootprint,
            BuildingType,
            WorldCoordinate,
        )

        coords = [
            WorldCoordinate(x=0, y=0, z=0),
            WorldCoordinate(x=20, y=0, z=0),
            WorldCoordinate(x=20, y=30, z=0),
            WorldCoordinate(x=0, y=30, z=0),
        ]

        building = BuildingFootprint(
            osm_id=67890,
            name="Test Tower",
            building_type=BuildingType.OFFICE,
            coordinates=coords,
            height=50.0,
            levels=12,
            outline=coords,
        )

        assert building.building_type == BuildingType.OFFICE
        compare_numbers(building.height, 50.0)
        assert building.levels == 12

    def test_building_center_calculation(self):
        """Building center should be calculated from footprint."""
        from lib.charlotte_digital_twin.geometry.types import (
            BuildingFootprint,
            BuildingType,
            WorldCoordinate,
        )

        coords = [
            WorldCoordinate(x=0, y=0, z=0),
            WorldCoordinate(x=20, y=0, z=0),
            WorldCoordinate(x=20, y=20, z=0),
            WorldCoordinate(x=0, y=20, z=0),
        ]

        building = BuildingFootprint(
            osm_id=1,
            name="Center Test",
            building_type=BuildingType.OFFICE,
            coordinates=coords,
            height=10.0,
            levels=3,
            outline=coords,
        )

        center = building.get_center()
        compare_numbers(center.x, 10.0, tolerance=0.1)
        compare_numbers(center.y, 10.0, tolerance=0.1)

    def test_building_area_calculation(self):
        """Building area should be calculated from footprint."""
        from lib.charlotte_digital_twin.geometry.types import (
            BuildingFootprint,
            BuildingType,
            WorldCoordinate,
        )

        coords = [
            WorldCoordinate(x=0, y=0, z=0),
            WorldCoordinate(x=10, y=0, z=0),
            WorldCoordinate(x=10, y=10, z=0),
            WorldCoordinate(x=0, y=10, z=0),
        ]

        building = BuildingFootprint(
            osm_id=1,
            name="Area Test",
            building_type=BuildingType.OFFICE,
            coordinates=coords,
            height=10.0,
            levels=3,
            outline=coords,
        )

        # Should be approximately 100 sq meters
        area = building.get_area()
        compare_numbers(area, 100.0, tolerance=1.0)


@pytest.mark.integration
class TestSceneAssembly:
    """Tests for scene assembly pipeline."""

    def test_scene_bounds_creation(self):
        """Scene bounds should be created from coordinates."""
        from lib.charlotte_digital_twin.geometry.types import SceneBounds

        bounds = SceneBounds(
            min_lat=35.2171,
            max_lat=35.2371,
            min_lon=-80.8531,
            max_lon=-80.8331,
        )

        # Should contain Charlotte downtown
        assert bounds.contains(35.2271, -80.8431)

    def test_scene_builder_config(self):
        """Scene builder should accept configuration."""
        from lib.charlotte_digital_twin.geometry.types import (
            GeometryConfig,
            DetailLevel,
            SceneOrigin,
        )

        origin = SceneOrigin(
            lat=35.2271,
            lon=-80.8431,
            name="Charlotte Downtown",
        )

        config = GeometryConfig(
            origin=origin,
            scale=1.0,
            detail_level=DetailLevel.STANDARD,
        )

        assert config.detail_level == DetailLevel.STANDARD
        compare_numbers(config.scale, 1.0)


@pytest.mark.integration
@pytest.mark.requires_blender
class TestSDProjectionPipeline:
    """Tests for SD projection mapping pipeline.

    Note: These tests require bpy (Blender) as the sd_projection modules
    import bpy at module level.
    """

    def test_style_config_creation(self):
        """Style configuration should be created with expected values."""
        pytest.skip("Requires Blender (bpy module)")

    def test_controlnet_config(self):
        """ControlNet configuration should be created."""
        pytest.skip("Requires Blender (bpy module)")

    def test_drift_config_integration(self):
        """Drift configuration should integrate with style blender."""
        pytest.skip("Requires Blender (bpy module)")

    def test_building_lod_config(self):
        """Building LOD should be configurable."""
        pytest.skip("Requires Blender (bpy module)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])

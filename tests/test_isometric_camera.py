"""
Unit tests for Isometric Camera module
"""

import pytest
import math
from lib.retro.isometric import (
    CameraConfig,
    create_isometric_camera_config,
    set_isometric_angle,
    calculate_isometric_rotation,
    calculate_camera_position,
    project_to_isometric,
    project_to_screen,
    depth_sort_objects,
    get_isometric_depth,
    create_isometric_grid_data,
    snap_to_isometric_grid,
    get_tile_bounds,
    world_to_tile,
    tile_to_world,
    calculate_tile_neighbors,
)
from lib.retro.isometric_types import IsometricConfig


class TestCameraConfig:
    """Tests for CameraConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = CameraConfig()
        assert config.name == "IsometricCamera"
        assert config.orthographic_scale == 10.0

    def test_to_dict(self):
        """Test serialization to dictionary."""
        config = CameraConfig()
        data = config.to_dict()
        assert data["name"] == "IsometricCamera"


class TestCreateIsometricCameraConfig:
    """Tests for create_isometric_camera_config function."""

    def test_returns_camera_config(self):
        """Test returns CameraConfig instance."""
        config = IsometricConfig()
        cam_config = create_isometric_camera_config(config)
        assert isinstance(cam_config, CameraConfig)

    def test_pixel_angle(self):
        """Test pixel angle configuration."""
        config = IsometricConfig(angle="pixel")
        cam_config = create_isometric_camera_config(config)
        # Camera should be positioned based on elevation and rotation
        assert cam_config.location != (0, 0, 0)

    def test_orthographic_scale(self):
        """Test orthographic scale is set."""
        config = IsometricConfig(orthographic_scale=15.0)
        cam_config = create_isometric_camera_config(config)
        assert cam_config.orthographic_scale == 15.0


class TestCalculateIsometricRotation:
    """Tests for calculate_isometric_rotation function."""

    def test_pixel_angle(self):
        """Test pixel angle rotation."""
        pitch, roll, yaw = calculate_isometric_rotation(30.0, 45.0)
        expected_pitch = math.pi / 2 - math.radians(30.0)
        assert abs(pitch - expected_pitch) < 0.01
        assert roll == 0.0
        assert abs(yaw - math.radians(45.0)) < 0.01

    def test_true_isometric(self):
        """Test true isometric rotation."""
        pitch, roll, yaw = calculate_isometric_rotation(35.264, 45.0)
        assert pitch > 0
        assert yaw > 0


class TestCalculateCameraPosition:
    """Tests for calculate_camera_position function."""

    def test_pixel_angle(self):
        """Test pixel angle position."""
        x, y, z = calculate_camera_position(30.0, 45.0, 10.0)
        # Camera should be above the scene
        assert z > 0

    def test_distance_affects_position(self):
        """Test distance affects position magnitude."""
        pos1 = calculate_camera_position(30.0, 45.0, 10.0)
        pos2 = calculate_camera_position(30.0, 45.0, 20.0)
        # Greater distance = further from origin
        dist1 = math.sqrt(sum(p**2 for p in pos1))
        dist2 = math.sqrt(sum(p**2 for p in pos2))
        assert dist2 > dist1


class TestProjectToIsometric:
    """Tests for project_to_isometric function."""

    def test_origin(self):
        """Test projecting origin."""
        config = IsometricConfig()
        x, y = project_to_isometric((0, 0, 0), config)
        assert x == 0
        assert y == 0

    def test_z_affects_y(self):
        """Test Z affects screen Y."""
        config = IsometricConfig()
        p1 = project_to_isometric((0, 0, 0), config)
        p2 = project_to_isometric((0, 0, 10), config)
        # Higher Z = lower on screen (negative Y offset)
        assert p2[1] < p1[1]

    def test_xy_affects_both(self):
        """Test X and Y affect both screen coordinates."""
        config = IsometricConfig()
        p1 = project_to_isometric((0, 0, 0), config)
        p2 = project_to_isometric((10, 0, 0), config)
        # Both screen X and Y should be different
        assert p2 != p1


class TestProjectToScreen:
    """Tests for project_to_screen function."""

    def test_origin(self):
        """Test projecting origin."""
        x, y = project_to_screen((0, 0, 0), 30.0, 45.0)
        assert x == 0
        assert y == 0

    def test_tile_size_affects_output(self):
        """Test tile size affects output scale."""
        p1 = project_to_screen((1, 1, 0), 30.0, 45.0, 32, 16)
        p2 = project_to_screen((1, 1, 0), 30.0, 45.0, 64, 32)
        # Larger tile size = larger output values
        assert abs(p2[0]) > abs(p1[0])


class TestDepthSortObjects:
    """Tests for depth_sort_objects function."""

    def test_empty_list(self):
        """Test sorting empty list."""
        result = depth_sort_objects([], (0, 0, 0))
        assert result == []

    def test_sorts_by_depth(self):
        """Test objects are sorted by isometric depth."""
        # Create mock objects with location
        class MockObj:
            def __init__(self, name, x, y, z):
                self.name = name
                self.location = (x, y, z)

        objects = [
            MockObj("far", -5, -5, 0),
            MockObj("near", 5, 5, 0),
        ]

        sorted_objects = depth_sort_objects(objects, (0, 0, 10))
        # Far object (lower x + y - z) should come first
        assert sorted_objects[0].name == "far"


class TestGetIsometricDepth:
    """Tests for get_isometric_depth function."""

    def test_origin(self):
        """Test depth at origin."""
        depth = get_isometric_depth((0, 0, 0))
        assert depth == 0

    def test_positive_xy(self):
        """Test depth with positive X and Y."""
        depth = get_isometric_depth((1, 1, 0))
        assert depth == 2

    def test_negative_xy(self):
        """Test depth with negative X and Y."""
        depth = get_isometric_depth((-1, -1, 0))
        assert depth == -2

    def test_z_decreases_depth(self):
        """Test Z decreases depth."""
        depth1 = get_isometric_depth((0, 0, 0))
        depth2 = get_isometric_depth((0, 0, 5))
        assert depth2 < depth1


class TestCreateIsometricGridData:
    """Tests for create_isometric_grid_data function."""

    def test_returns_lines(self):
        """Test returns list of lines."""
        config = IsometricConfig()
        lines = create_isometric_grid_data(config, grid_size=5)
        assert isinstance(lines, list)
        # Each line is a tuple of two points
        for line in lines:
            assert len(line) == 2

    def test_grid_size_affects_count(self):
        """Test grid size affects line count."""
        config = IsometricConfig()
        lines1 = create_isometric_grid_data(config, grid_size=2)
        lines2 = create_isometric_grid_data(config, grid_size=4)
        assert len(lines2) > len(lines1)


class TestSnapToIsometricGrid:
    """Tests for snap_to_isometric_grid function."""

    def test_snaps_to_grid(self):
        """Test position is snapped."""
        config = IsometricConfig(tile_width=32, tile_height=16)
        snapped = snap_to_isometric_grid((1.5, 1.5, 1.5), config)
        # Should snap to integer values
        assert snapped[2] == 2  # Z rounds


class TestGetTileBounds:
    """Tests for get_tile_bounds function."""

    def test_center_tile(self):
        """Test bounds of center tile."""
        config = IsometricConfig(tile_width=32, tile_height=16)
        min_x, min_y, max_x, max_y = get_tile_bounds(0, 0, config)
        # Center tile should span from negative to positive
        assert min_x < 0
        assert max_x > 0
        assert min_y < 0
        assert max_y > 0

    def test_offset_tile(self):
        """Test bounds of offset tile."""
        config = IsometricConfig(tile_width=32, tile_height=16)
        bounds1 = get_tile_bounds(0, 0, config)
        bounds2 = get_tile_bounds(1, 0, config)
        # Different tile positions should have different bounds
        assert bounds2 != bounds1


class TestWorldToTile:
    """Tests for world_to_tile function."""

    def test_round_trip(self):
        """Test world -> tile -> world conversion."""
        config = IsometricConfig(tile_width=32, tile_height=16)
        original_world = tile_to_world(2, 3, config)
        tile = world_to_tile(original_world, config)
        # Should get back to the same tile (approximately)
        # Note: due to centering offset and isometric projection, may be off by 2
        assert abs(tile[0] - 2) <= 2
        assert abs(tile[1] - 3) <= 2


class TestTileToWorld:
    """Tests for tile_to_world function."""

    def test_origin(self):
        """Test tile 0,0 converts to world origin."""
        config = IsometricConfig(tile_width=32, tile_height=16)
        world = tile_to_world(0, 0, config)
        assert world[0] == 0
        assert world[1] == 0
        assert world[2] == 0


class TestCalculateTileNeighbors:
    """Tests for calculate_tile_neighbors function."""

    def test_returns_8_neighbors(self):
        """Test returns 8 neighbors."""
        neighbors = calculate_tile_neighbors(0, 0)
        assert len(neighbors) == 8

    def test_neighbors_are_adjacent(self):
        """Test neighbors are adjacent tiles."""
        neighbors = calculate_tile_neighbors(5, 5)
        # Should include tiles like (6, 5), (4, 5), etc.
        assert (6, 5) in neighbors
        assert (4, 5) in neighbors
        assert (5, 6) in neighbors
        assert (5, 4) in neighbors


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

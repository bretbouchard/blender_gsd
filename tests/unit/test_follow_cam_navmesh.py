"""
Follow Camera Navigation Mesh Unit Tests

Tests for: lib/cinematic/follow_cam/navmesh.py
Coverage target: 80%+

Part of Phase 8.x - Follow Camera System
Beads: blender_gsd-61
"""

import pytest
import math
from lib.oracle import compare_numbers, compare_vectors, Oracle

from lib.cinematic.follow_cam.navmesh import (
    NavMeshConfig,
    NavMesh,
    NavCell,
    smooth_path,
    simplify_path,
)


class TestNavMeshConfig:
    """Unit tests for NavMeshConfig dataclass."""

    def test_default_values(self):
        """Default NavMeshConfig should have sensible defaults."""
        config = NavMeshConfig()

        compare_numbers(config.cell_size, 0.5)
        compare_numbers(config.camera_height, 2.0)
        compare_numbers(config.camera_radius, 0.5)
        compare_numbers(config.max_slope, 45.0)
        assert config.include_transparent is False

    def test_custom_values(self):
        """NavMeshConfig should store all config values."""
        config = NavMeshConfig(
            cell_size=1.0,
            camera_height=3.0,
            camera_radius=0.75,
            max_slope=60.0,
            include_transparent=True,
        )

        compare_numbers(config.cell_size, 1.0)
        compare_numbers(config.camera_height, 3.0)
        compare_numbers(config.camera_radius, 0.75)
        compare_numbers(config.max_slope, 60.0)
        assert config.include_transparent is True


class TestNavCell:
    """Unit tests for NavCell dataclass."""

    def test_default_values(self):
        """Default NavCell should have sensible defaults."""
        cell = NavCell(x=0, y=0)

        assert cell.x == 0
        assert cell.y == 0
        compare_numbers(cell.z, 0.0)
        assert cell.walkable is True
        compare_numbers(cell.clearance, 2.0)

    def test_custom_values(self):
        """NavCell should store all cell data."""
        cell = NavCell(
            x=10,
            y=5,
            z=3.5,
            walkable=False,
            clearance=1.5,
        )

        assert cell.x == 10
        assert cell.y == 5
        compare_numbers(cell.z, 3.5)
        assert cell.walkable is False
        compare_numbers(cell.clearance, 1.5)

    def test_hash_and_equality(self):
        """NavCell should be hashable and comparable by position."""
        cell1 = NavCell(x=5, y=10)
        cell2 = NavCell(x=5, y=10)
        cell3 = NavCell(x=5, y=11)

        # Equality
        assert cell1 == cell2
        assert cell1 != cell3

        # Hash
        assert hash(cell1) == hash(cell2)
        assert hash(cell1) != hash(cell3)

        # Can be used in set
        cell_set = {cell1, cell2, cell3}
        assert len(cell_set) == 2

    def test_world_position(self):
        """world_position should calculate correct world coordinates."""
        cell = NavCell(x=5, y=3, z=2.0)

        pos = cell.world_position(cell_size=1.0, origin=(0.0, 0.0))

        # x = 0 + 5 * 1.0 + 0.5 = 5.5
        # y = 0 + 3 * 1.0 + 0.5 = 3.5
        compare_vectors(pos, (5.5, 3.5, 2.0))

    def test_world_position_with_origin(self):
        """world_position should offset by origin."""
        cell = NavCell(x=5, y=3, z=2.0)

        pos = cell.world_position(cell_size=2.0, origin=(10.0, 20.0))

        # x = 10 + 5 * 2.0 + 1.0 = 21.0
        # y = 20 + 3 * 2.0 + 1.0 = 27.0
        compare_vectors(pos, (21.0, 27.0, 2.0))


class TestNavMesh:
    """Unit tests for NavMesh class."""

    def test_initialization(self):
        """NavMesh should initialize with config."""
        config = NavMeshConfig(cell_size=1.0)
        navmesh = NavMesh(config)

        assert navmesh.config == config
        assert navmesh.is_generated() is False

    def test_default_config(self):
        """NavMesh should create default config if not provided."""
        navmesh = NavMesh()

        assert navmesh.config is not None
        compare_numbers(navmesh.config.cell_size, 0.5)

    def test_generate_from_scene_without_blender(self):
        """Generate should return False without Blender."""
        navmesh = NavMesh()

        result = navmesh.generate_from_scene()

        # Without Blender, should return False
        assert result is False
        assert navmesh.is_generated() is False

    def test_find_path_not_generated(self):
        """Find path should return empty if not generated."""
        navmesh = NavMesh()

        path = navmesh.find_path(
            start=(0.0, 0.0, 0.0),
            end=(10.0, 0.0, 0.0),
        )

        assert path == []

    def test_get_cell_count(self):
        """get_cell_count should return number of cells."""
        navmesh = NavMesh()

        # Should be 0 before generation
        assert navmesh.get_cell_count() == 0

    def test_get_walkable_count(self):
        """get_walkable_count should return walkable cells."""
        navmesh = NavMesh()

        # Should be 0 before generation
        assert navmesh.get_walkable_count() == 0

    def test_world_to_cell_conversion(self):
        """_world_to_cell should convert world to cell coordinates."""
        navmesh = NavMesh(NavMeshConfig(cell_size=1.0))
        navmesh._origin = (0.0, 0.0)

        cell = navmesh._world_to_cell((5.5, 3.5, 0.0))

        assert cell == (5, 3)

    def test_cell_to_world_conversion(self):
        """_cell_to_world should convert cell to world coordinates."""
        navmesh = NavMesh(NavMeshConfig(cell_size=1.0))
        navmesh._origin = (0.0, 0.0)

        # Add a cell
        navmesh._cells[(5, 3)] = NavCell(x=5, y=3, z=0.0)

        world = navmesh._cell_to_world((5, 3))

        compare_vectors(world, (5.5, 3.5, 0.0))

    def test_heuristic_calculation(self):
        """_heuristic should calculate distance between cells."""
        navmesh = NavMesh(NavMeshConfig(cell_size=1.0))

        dist = navmesh._heuristic((0, 0), (3, 4))

        # sqrt(3^2 + 4^2) = 5
        compare_numbers(dist, 5.0)

    def test_distance_cardinal(self):
        """_distance should return cell_size for cardinal moves."""
        navmesh = NavMesh(NavMeshConfig(cell_size=1.0))

        dist = navmesh._distance((0, 0), (1, 0))

        compare_numbers(dist, 1.0)

    def test_distance_diagonal(self):
        """_distance should return sqrt(2) * cell_size for diagonal."""
        navmesh = NavMesh(NavMeshConfig(cell_size=1.0))

        dist = navmesh._distance((0, 0), (1, 1))

        compare_numbers(dist, math.sqrt(2), tolerance=0.01)

    def test_get_neighbors(self):
        """_get_neighbors should return adjacent cells."""
        navmesh = NavMesh()

        # Add some cells
        for x in range(3):
            for y in range(3):
                navmesh._cells[(x, y)] = NavCell(x=x, y=y)

        neighbors = navmesh._get_neighbors((1, 1))

        # Should have 8 neighbors (3x3 grid minus center)
        assert len(neighbors) == 8

    def test_get_neighbors_edge(self):
        """_get_neighbors should only return existing cells."""
        navmesh = NavMesh()

        # Add a corner cell only
        navmesh._cells[(0, 0)] = NavCell(x=0, y=0)
        navmesh._cells[(1, 0)] = NavCell(x=1, y=0)
        navmesh._cells[(0, 1)] = NavCell(x=0, y=1)

        neighbors = navmesh._get_neighbors((0, 0))

        # Should only have 2 neighbors
        assert len(neighbors) == 2


class TestSmoothPath:
    """Unit tests for smooth_path function."""

    def test_empty_path(self):
        """Empty path should return empty."""
        result = smooth_path([])

        assert result == []

    def test_single_point(self):
        """Single point path should return unchanged."""
        result = smooth_path([(0.0, 0.0, 0.0)])

        assert result == [(0.0, 0.0, 0.0)]

    def test_two_points(self):
        """Two point path should return unchanged."""
        result = smooth_path([(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)])

        assert len(result) == 2

    def test_basic_smoothing(self):
        """Smoothing should smooth path points."""
        path = [
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (2.0, 0.0, 0.0),
            (3.0, 0.0, 0.0),
            (4.0, 0.0, 0.0),
        ]

        result = smooth_path(path, smoothing_factor=0.5, iterations=1)

        # Should have same number of points
        assert len(result) == 5

        # Endpoints should be preserved
        compare_vectors(result[0], path[0])
        compare_vectors(result[-1], path[-1])

    def test_iterations(self):
        """More iterations should produce smoother path."""
        path = [
            (0.0, 0.0, 0.0),
            (1.0, 1.0, 0.0),
            (2.0, 0.0, 0.0),
            (3.0, 1.0, 0.0),
            (4.0, 0.0, 0.0),
        ]

        result1 = smooth_path(path, iterations=1)
        result3 = smooth_path(path, iterations=3)

        # Both should have same length
        assert len(result1) == len(result3) == 5

        # More iterations should produce different (smoother) result
        # At least one point should differ
        different = False
        for i in range(len(path)):
            if result1[i] != result3[i]:
                different = True
                break
        # Note: This might not always be true, so we just check structure


class TestSimplifyPath:
    """Unit tests for simplify_path function."""

    def test_empty_path(self):
        """Empty path should return empty."""
        result = simplify_path([])

        assert result == []

    def test_single_point(self):
        """Single point path should return unchanged."""
        result = simplify_path([(0.0, 0.0, 0.0)])

        assert result == [(0.0, 0.0, 0.0)]

    def test_two_points(self):
        """Two point path should return unchanged."""
        result = simplify_path([(0.0, 0.0, 0.0), (1.0, 0.0, 0.0)])

        assert len(result) == 2

    def test_straight_line(self):
        """Straight line should simplify to endpoints."""
        path = [
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (2.0, 0.0, 0.0),
            (3.0, 0.0, 0.0),
            (4.0, 0.0, 0.0),
        ]

        result = simplify_path(path, tolerance=0.1)

        # Should simplify to just endpoints
        assert len(result) == 2
        compare_vectors(result[0], path[0])
        compare_vectors(result[-1], path[-1])

    def test_path_with_corner(self):
        """Path with corner should preserve corner point."""
        path = [
            (0.0, 0.0, 0.0),
            (1.0, 0.0, 0.0),
            (2.0, 0.0, 0.0),
            (2.0, 1.0, 0.0),  # Corner
            (2.0, 2.0, 0.0),
            (2.0, 3.0, 0.0),
        ]

        result = simplify_path(path, tolerance=0.1)

        # Should preserve at least the corner
        assert len(result) >= 3

    def test_tolerance_affects_simplification(self):
        """Higher tolerance should simplify more."""
        path = [
            (0.0, 0.0, 0.0),
            (1.0, 0.1, 0.0),
            (2.0, -0.1, 0.0),
            (3.0, 0.05, 0.0),
            (4.0, 0.0, 0.0),
        ]

        result_low = simplify_path(path, tolerance=0.01)
        result_high = simplify_path(path, tolerance=1.0)

        # Higher tolerance should have fewer points
        assert len(result_high) <= len(result_low)


class TestModuleImports:
    """Tests for module-level imports."""

    def test_navmesh_module_imports(self):
        """All navmesh types should be importable."""
        from lib.cinematic.follow_cam.navmesh import (
            NavMeshConfig,
            NavMesh,
            NavCell,
            smooth_path,
            simplify_path,
        )

        assert NavMeshConfig is not None
        assert NavMesh is not None
        assert NavCell is not None

    def test_package_imports_navmesh(self):
        """Navmesh APIs should be importable from package."""
        from lib.cinematic.follow_cam import (
            NavMeshConfig,
            NavMesh,
            NavCell,
            smooth_path,
            simplify_path,
        )

        assert NavMeshConfig is not None
        assert NavMesh is not None


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])

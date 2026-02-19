"""
Surface Detection Unit Tests

Tests for: lib/cinematic/projection/surface_detection.py
Coverage target: 80%+

Part of Phase 9.1 - Surface Detection (REQ-ANAM-02)
Beads: blender_gsd-35
"""

import pytest
from lib.oracle import compare_numbers, compare_vectors

from lib.cinematic.projection.types import (
    SurfaceType,
    SurfaceInfo,
    FrustumConfig,
)

from lib.cinematic.projection.surface_detection import (
    OcclusionResult,
    MultiSurfaceGroup,
    SurfaceSelectionMask,
    filter_surfaces_by_type,
    get_best_projection_surfaces,
    detect_multi_surface_groups,
)


class TestOcclusionResult:
    """Unit tests for OcclusionResult dataclass."""

    def test_default_values(self):
        """Default OcclusionResult should have sensible defaults."""
        surface = SurfaceInfo(object_name="Floor", surface_type=SurfaceType.FLOOR)
        result = OcclusionResult(
            surface=surface,
            is_occluded=False,
            occlusion_ratio=0.0,
        )

        assert result.surface == surface
        assert result.is_occluded is False
        assert result.occlusion_ratio == 0.0
        assert result.occluding_objects == []
        assert result.visible_face_count == 0
        assert result.total_face_count == 0

    def test_occluded_surface(self):
        """Occluded surface should have high occlusion ratio."""
        surface = SurfaceInfo(object_name="HiddenFloor", surface_type=SurfaceType.FLOOR)
        result = OcclusionResult(
            surface=surface,
            is_occluded=True,
            occlusion_ratio=0.95,
            occluding_objects=["Wall", "Table"],
            visible_face_count=5,
            total_face_count=100,
        )

        assert result.is_occluded is True
        compare_numbers(result.occlusion_ratio, 0.95)
        assert len(result.occluding_objects) == 2
        assert result.visible_face_count == 5


class TestMultiSurfaceGroup:
    """Unit tests for MultiSurfaceGroup dataclass."""

    def test_single_surface_group(self):
        """Single surface group should work."""
        surface = SurfaceInfo(
            object_name="Floor",
            surface_type=SurfaceType.FLOOR,
            center=(0.0, 0.0, 0.0),
            area=10.0,
        )

        group = MultiSurfaceGroup(
            surfaces=[surface],
            group_type="floor",
            total_area=10.0,
            center=(0.0, 0.0, 0.0),
            has_uv_continuity=True,
        )

        assert len(group.surfaces) == 1
        assert group.group_type == "floor"
        compare_numbers(group.total_area, 10.0)

    def test_corner_group(self):
        """Corner group should combine floor and wall."""
        floor = SurfaceInfo(
            object_name="Floor",
            surface_type=SurfaceType.FLOOR,
            center=(0.0, 0.0, 0.0),
            area=10.0,
        )
        wall = SurfaceInfo(
            object_name="Wall",
            surface_type=SurfaceType.WALL,
            center=(0.0, 0.0, 1.5),
            area=8.0,
        )

        group = MultiSurfaceGroup(
            surfaces=[floor, wall],
            group_type="corner",
            total_area=18.0,
            center=(0.0, 0.0, 0.75),
            has_uv_continuity=False,
        )

        assert len(group.surfaces) == 2
        assert group.group_type == "corner"
        compare_numbers(group.total_area, 18.0)


class TestSurfaceSelectionMask:
    """Unit tests for SurfaceSelectionMask dataclass."""

    def test_default_values(self):
        """Default mask should be empty."""
        mask = SurfaceSelectionMask(
            object_name="Floor",
            selected_faces=[],
            mask_bounds=((0, 0, 0), (1, 1, 1)),
            mask_area=0.0,
        )

        assert mask.object_name == "Floor"
        assert mask.selected_faces == []
        assert mask.mask_area == 0.0

    def test_partial_mask(self):
        """Partial surface mask should track selected faces."""
        mask = SurfaceSelectionMask(
            object_name="Wall",
            selected_faces=[0, 1, 2, 5, 6, 7],
            mask_bounds=((-1, -1, 0), (1, 1, 3)),
            mask_area=5.5,
        )

        assert len(mask.selected_faces) == 6
        compare_numbers(mask.mask_area, 5.5)
        assert mask.mask_bounds[0] == (-1, -1, 0)


class TestFilterSurfacesByType:
    """Unit tests for filter_surfaces_by_type function."""

    def test_filter_floor_only(self):
        """Should return only floor surfaces."""
        surfaces = [
            SurfaceInfo(object_name="Floor1", surface_type=SurfaceType.FLOOR),
            SurfaceInfo(object_name="Wall1", surface_type=SurfaceType.WALL),
            SurfaceInfo(object_name="Floor2", surface_type=SurfaceType.FLOOR),
            SurfaceInfo(object_name="Ceiling1", surface_type=SurfaceType.CEILING),
        ]

        floors = filter_surfaces_by_type(surfaces, [SurfaceType.FLOOR])

        assert len(floors) == 2
        assert all(s.surface_type == SurfaceType.FLOOR for s in floors)

    def test_filter_multiple_types(self):
        """Should return floor and wall surfaces."""
        surfaces = [
            SurfaceInfo(object_name="Floor1", surface_type=SurfaceType.FLOOR),
            SurfaceInfo(object_name="Wall1", surface_type=SurfaceType.WALL),
            SurfaceInfo(object_name="Ceiling1", surface_type=SurfaceType.CEILING),
        ]

        horizontal = filter_surfaces_by_type(
            surfaces, [SurfaceType.FLOOR, SurfaceType.WALL]
        )

        assert len(horizontal) == 2
        assert SurfaceType.CEILING not in [s.surface_type for s in horizontal]

    def test_filter_empty_input(self):
        """Empty input should return empty output."""
        result = filter_surfaces_by_type([], [SurfaceType.FLOOR])
        assert result == []

    def test_filter_no_match(self):
        """No matching types should return empty list."""
        surfaces = [
            SurfaceInfo(object_name="Floor1", surface_type=SurfaceType.FLOOR),
        ]

        result = filter_surfaces_by_type(surfaces, [SurfaceType.CEILING])
        assert result == []


class TestGetBestProjectionSurfaces:
    """Unit tests for get_best_projection_surfaces function."""

    def test_sort_by_area(self):
        """Should sort surfaces by area (largest first)."""
        surfaces = [
            SurfaceInfo(
                object_name="SmallFloor",
                surface_type=SurfaceType.FLOOR,
                area=1.0,
                in_frustum=True,
            ),
            SurfaceInfo(
                object_name="LargeFloor",
                surface_type=SurfaceType.FLOOR,
                area=10.0,
                in_frustum=True,
            ),
            SurfaceInfo(
                object_name="MediumFloor",
                surface_type=SurfaceType.FLOOR,
                area=5.0,
                in_frustum=True,
            ),
        ]

        best = get_best_projection_surfaces(surfaces, "Camera")

        assert len(best) == 3
        assert best[0].object_name == "LargeFloor"
        assert best[1].object_name == "MediumFloor"
        assert best[2].object_name == "SmallFloor"

    def test_prefer_type(self):
        """Should prefer specified type over area."""
        surfaces = [
            SurfaceInfo(
                object_name="LargeWall",
                surface_type=SurfaceType.WALL,
                area=20.0,
                in_frustum=True,
            ),
            SurfaceInfo(
                object_name="SmallFloor",
                surface_type=SurfaceType.FLOOR,
                area=1.0,
                in_frustum=True,
            ),
        ]

        best = get_best_projection_surfaces(
            surfaces, "Camera", prefer_type=SurfaceType.FLOOR
        )

        assert best[0].surface_type == SurfaceType.FLOOR
        assert best[1].surface_type == SurfaceType.WALL

    def test_filter_by_min_area(self):
        """Should filter out surfaces below minimum area."""
        surfaces = [
            SurfaceInfo(
                object_name="TinyFloor",
                surface_type=SurfaceType.FLOOR,
                area=0.05,
                in_frustum=True,
            ),
            SurfaceInfo(
                object_name="BigFloor",
                surface_type=SurfaceType.FLOOR,
                area=5.0,
                in_frustum=True,
            ),
        ]

        best = get_best_projection_surfaces(surfaces, "Camera", min_area=0.1)

        assert len(best) == 1
        assert best[0].object_name == "BigFloor"

    def test_filter_out_of_frustum(self):
        """Should filter out surfaces not in frustum."""
        surfaces = [
            SurfaceInfo(
                object_name="VisibleFloor",
                surface_type=SurfaceType.FLOOR,
                area=5.0,
                in_frustum=True,
            ),
            SurfaceInfo(
                object_name="HiddenFloor",
                surface_type=SurfaceType.FLOOR,
                area=10.0,
                in_frustum=False,
            ),
        ]

        best = get_best_projection_surfaces(surfaces, "Camera")

        assert len(best) == 1
        assert best[0].object_name == "VisibleFloor"


class TestDetectMultiSurfaceGroups:
    """Unit tests for detect_multi_surface_groups function."""

    def test_single_surfaces(self):
        """Single surfaces should each become a group."""
        surfaces = [
            SurfaceInfo(
                object_name="Floor",
                surface_type=SurfaceType.FLOOR,
                center=(0.0, 0.0, 0.0),
                area=10.0,
            ),
            SurfaceInfo(
                object_name="Wall",
                surface_type=SurfaceType.WALL,
                center=(0.0, 0.0, 1.5),
                area=8.0,
            ),
        ]

        groups = detect_multi_surface_groups(surfaces, max_gap=0.5)

        # Should have at least 2 groups (one per surface)
        # May also have corner group if they form a corner
        assert len(groups) >= 2

        # Check single-surface groups exist
        single_groups = [g for g in groups if len(g.surfaces) == 1]
        assert len(single_groups) == 2

    def test_empty_surfaces(self):
        """Empty input should return empty output."""
        groups = detect_multi_surface_groups([])
        assert groups == []

    def test_corner_detection(self):
        """Should detect floor + wall corners."""
        floor = SurfaceInfo(
            object_name="Floor",
            surface_type=SurfaceType.FLOOR,
            center=(0.0, 0.0, 0.0),
            area=10.0,
        )
        wall = SurfaceInfo(
            object_name="Wall",
            surface_type=SurfaceType.WALL,
            center=(0.0, 0.0, 1.5),  # Near floor level
            area=8.0,
        )

        groups = detect_multi_surface_groups([floor, wall], max_gap=2.0)

        # Should include a corner group
        corner_groups = [g for g in groups if g.group_type == "corner"]
        assert len(corner_groups) >= 1


class TestModuleImports:
    """Tests for module-level imports."""

    def test_surface_detection_imports(self):
        """All surface detection types should be importable."""
        from lib.cinematic.projection.surface_detection import (
            OcclusionResult,
            MultiSurfaceGroup,
            SurfaceSelectionMask,
            detect_surfaces,
            detect_occlusion,
            detect_multi_surface_groups,
            create_surface_selection_mask,
            filter_surfaces_by_type,
            get_best_projection_surfaces,
        )

        assert OcclusionResult is not None
        assert MultiSurfaceGroup is not None
        assert SurfaceSelectionMask is not None
        assert callable(detect_surfaces)
        assert callable(detect_occlusion)
        assert callable(filter_surfaces_by_type)

    def test_package_imports(self):
        """All surface detection APIs should be importable from package."""
        from lib.cinematic.projection import (
            OcclusionResult,
            MultiSurfaceGroup,
            SurfaceSelectionMask,
            detect_surfaces,
            detect_occlusion,
            detect_multi_surface_groups,
            create_surface_selection_mask,
            filter_surfaces_by_type,
            get_best_projection_surfaces,
        )

        assert OcclusionResult is not None
        assert MultiSurfaceGroup is not None
        assert callable(detect_surfaces)
        assert callable(filter_surfaces_by_type)


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])

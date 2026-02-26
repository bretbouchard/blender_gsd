"""
Unit tests for projection target types.

Tests for TargetType, SurfaceMaterial enums and ProjectionSurface,
ProjectionTarget dataclasses.
"""

import pytest
from lib.cinematic.projection.physical.targets import (
    TargetType,
    SurfaceMaterial,
    ProjectionSurface,
    ProjectionTarget,
    TargetGeometryResult,
    PLANAR_2X2M,
    GARAGE_DOOR_STANDARD,
)


class TestTargetType:
    """Tests for TargetType enum."""

    def test_all_types_defined(self):
        """All target types are defined."""
        assert TargetType.PLANAR.value == "planar"
        assert TargetType.MULTI_SURFACE.value == "multi_surface"
        assert TargetType.CURVED.value == "curved"
        assert TargetType.IRREGULAR.value == "irregular"

    def test_type_count(self):
        """Expected number of target types."""
        assert len(TargetType) == 4


class TestSurfaceMaterial:
    """Tests for SurfaceMaterial enum."""

    def test_common_materials(self):
        """Common materials are defined."""
        assert SurfaceMaterial.WHITE_PAINT.value == "white_paint"
        assert SurfaceMaterial.GRAY_PAINT.value == "gray_paint"
        assert SurfaceMaterial.PROJECTOR_SCREEN.value == "screen"

    def test_material_count(self):
        """Expected number of materials."""
        assert len(SurfaceMaterial) >= 8


class TestProjectionSurface:
    """Tests for ProjectionSurface dataclass."""

    def test_default_surface(self):
        """Create surface with defaults."""
        surface = ProjectionSurface(
            name="test",
            surface_type=TargetType.PLANAR,
        )

        assert surface.name == "test"
        assert surface.surface_type == TargetType.PLANAR
        assert surface.position == (0.0, 0.0, 0.0)
        assert surface.dimensions == (1.0, 1.0)
        assert surface.material == SurfaceMaterial.WHITE_PAINT
        assert surface.albedo == 0.85
        assert surface.glossiness == 0.1

    def test_custom_surface(self):
        """Create surface with custom values."""
        surface = ProjectionSurface(
            name="custom",
            surface_type=TargetType.PLANAR,
            position=(1.0, 2.0, 3.0),
            dimensions=(4.0, 2.0),
            material=SurfaceMaterial.PROJECTOR_SCREEN,
            albedo=0.95,
            glossiness=0.3,
        )

        assert surface.position == (1.0, 2.0, 3.0)
        assert surface.dimensions == (4.0, 2.0)
        assert surface.material == SurfaceMaterial.PROJECTOR_SCREEN
        assert surface.albedo == 0.95
        assert surface.glossiness == 0.3

    def test_surface_serialization(self):
        """Test to_dict and from_dict."""
        surface = ProjectionSurface(
            name="serialize_test",
            surface_type=TargetType.PLANAR,
            position=(1.5, 2.5, 3.5),
            dimensions=(2.0, 3.0),
            albedo=0.7,
            calibration_points=[(0, 0, 0), (1, 0, 0), (0, 1, 0)],
        )

        data = surface.to_dict()
        restored = ProjectionSurface.from_dict(data)

        assert restored.name == surface.name
        assert restored.position == surface.position
        assert restored.dimensions == surface.dimensions
        assert restored.albedo == surface.albedo
        assert len(restored.calibration_points) == 3

    def test_compute_default_calibration_points(self):
        """Default calibration points are computed correctly."""
        surface = ProjectionSurface(
            name="cal_test",
            surface_type=TargetType.PLANAR,
            position=(1.0, 0.0, 1.0),
            dimensions=(2.0, 2.0),
        )

        points = surface.compute_default_calibration_points()

        assert len(points) == 3  # 3-point calibration
        # Points should be at corners relative to position


class TestProjectionTarget:
    """Tests for ProjectionTarget dataclass."""

    def test_default_target(self):
        """Create target with defaults."""
        target = ProjectionTarget(
            name="test_target",
            description="Test target",
            target_type=TargetType.PLANAR,
        )

        assert target.name == "test_target"
        assert target.target_type == TargetType.PLANAR
        assert target.width_m == 1.0
        assert target.height_m == 1.0
        assert target.depth_m == 0.0
        assert target.recommended_calibration == "three_point"

    def test_multi_surface_target(self):
        """Create multi-surface target."""
        target = ProjectionTarget(
            name="multi",
            description="Multi-surface",
            target_type=TargetType.MULTI_SURFACE,
            surfaces=[
                ProjectionSurface(name="s1", surface_type=TargetType.PLANAR),
                ProjectionSurface(name="s2", surface_type=TargetType.PLANAR),
            ],
            width_m=4.0,
            height_m=3.0,
            depth_m=0.5,
        )

        assert len(target.surfaces) == 2
        assert target.width_m == 4.0
        assert target.depth_m == 0.5

    def test_get_total_area(self):
        """Total area is computed correctly."""
        target = ProjectionTarget(
            name="area_test",
            description="Area test",
            target_type=TargetType.MULTI_SURFACE,
            surfaces=[
                ProjectionSurface(name="s1", surface_type=TargetType.PLANAR, area_m2=2.0),
                ProjectionSurface(name="s2", surface_type=TargetType.PLANAR, area_m2=3.0),
            ],
        )

        assert target.get_total_area() == 5.0

    def test_get_primary_surface(self):
        """Primary surface is largest."""
        target = ProjectionTarget(
            name="primary_test",
            description="Primary test",
            target_type=TargetType.MULTI_SURFACE,
            surfaces=[
                ProjectionSurface(name="small", surface_type=TargetType.PLANAR, area_m2=1.0),
                ProjectionSurface(name="large", surface_type=TargetType.PLANAR, area_m2=5.0),
                ProjectionSurface(name="medium", surface_type=TargetType.PLANAR, area_m2=3.0),
            ],
        )

        primary = target.get_primary_surface()
        assert primary.name == "large"

    def test_get_primary_surface_empty(self):
        """Primary surface is None when empty."""
        target = ProjectionTarget(
            name="empty",
            description="Empty",
            target_type=TargetType.PLANAR,
        )

        assert target.get_primary_surface() is None

    def test_target_serialization(self):
        """Test target serialization round-trip."""
        target = ProjectionTarget(
            name="serialize",
            description="Serialization test",
            target_type=TargetType.MULTI_SURFACE,
            surfaces=[
                ProjectionSurface(name="s1", surface_type=TargetType.PLANAR, area_m2=2.0),
            ],
            width_m=3.0,
            height_m=2.0,
            preset_measurements={"gap": 0.1},
        )

        data = target.to_dict()
        restored = ProjectionTarget.from_dict(data)

        assert restored.name == target.name
        assert restored.target_type == target.target_type
        assert len(restored.surfaces) == 1
        assert restored.width_m == 3.0
        assert restored.preset_measurements["gap"] == 0.1


class TestTargetGeometryResult:
    """Tests for TargetGeometryResult."""

    def test_default_result(self):
        """Default result is empty."""
        result = TargetGeometryResult()

        assert result.object is None
        assert result.surfaces == {}
        assert result.uv_layers == {}
        assert result.errors == []
        assert result.warnings == []

    def test_success_property(self):
        """Success property checks for errors and object."""
        result = TargetGeometryResult()
        assert not result.success  # No object

        result.object = "mock_object"
        assert result.success

        result.errors.append("Error")
        assert not result.success

    def test_to_dict(self):
        """Result serializes without Blender objects."""
        result = TargetGeometryResult(
            surfaces={"main": "mock"},
            uv_layers={"uv": "mock"},
            errors=["test error"],
        )

        data = result.to_dict()

        assert "surface_names" in data
        assert "main" in data["surface_names"]
        assert data["errors"] == ["test error"]


class TestPresetTargets:
    """Tests for preset target configurations."""

    def test_planar_2x2m_preset(self):
        """2x2m planar preset is correct."""
        assert PLANAR_2X2M.name == "planar_2x2m"
        assert PLANAR_2X2M.target_type == TargetType.PLANAR
        assert PLANAR_2X2M.width_m == 2.0
        assert PLANAR_2X2M.height_m == 2.0
        assert len(PLANAR_2X2M.surfaces) == 1
        assert PLANAR_2X2M.get_total_area() == 4.0

    def test_garage_door_preset(self):
        """Garage door preset is correct."""
        assert GARAGE_DOOR_STANDARD.name == "garage_door_standard"
        assert GARAGE_DOOR_STANDARD.target_type == TargetType.PLANAR
        assert GARAGE_DOOR_STANDARD.width_m == 4.88  # 16ft
        assert GARAGE_DOOR_STANDARD.height_m == 2.13  # 7ft
        assert len(GARAGE_DOOR_STANDARD.surfaces) == 1
        assert "frame_width" in GARAGE_DOOR_STANDARD.preset_measurements

"""
Unit tests for projection target builders.

Tests for TargetBuilder, PlanarTargetBuilder, MultiSurfaceTargetBuilder.
"""

import pytest
import math
from lib.cinematic.projection.physical.targets import (
    TargetType,
    ProjectionSurface,
    ProjectionTarget,
    TargetBuilder,
    PlanarTargetBuilder,
    MultiSurfaceTargetBuilder,
    create_builder,
    PLANAR_2X2M,
)


class TestPlanarTargetBuilder:
    """Tests for PlanarTargetBuilder."""

    @pytest.fixture
    def planar_target(self):
        """Create a simple planar target."""
        return ProjectionTarget(
            name="test_planar",
            description="Test planar target",
            target_type=TargetType.PLANAR,
            width_m=2.0,
            height_m=1.5,
        )

    @pytest.fixture
    def builder(self, planar_target):
        """Create builder for planar target."""
        return PlanarTargetBuilder(planar_target)

    def test_builder_initialization(self, builder, planar_target):
        """Builder initializes correctly."""
        assert builder.config == planar_target

    def test_validate_dimensions_valid(self, builder):
        """Valid dimensions pass validation."""
        errors = builder.validate_dimensions()
        assert len(errors) == 0

    def test_validate_dimensions_invalid_width(self):
        """Invalid width fails validation."""
        target = ProjectionTarget(
            name="invalid",
            description="Invalid",
            target_type=TargetType.PLANAR,
            width_m=-1.0,
            height_m=1.0,
        )
        builder = PlanarTargetBuilder(target)
        errors = builder.validate_dimensions()
        assert len(errors) > 0
        assert any("width" in e.lower() for e in errors)

    def test_validate_dimensions_invalid_height(self):
        """Invalid height fails validation."""
        target = ProjectionTarget(
            name="invalid",
            description="Invalid",
            target_type=TargetType.PLANAR,
            width_m=1.0,
            height_m=0.0,
        )
        builder = PlanarTargetBuilder(target)
        errors = builder.validate_dimensions()
        assert len(errors) > 0

    def test_validate_dimensions_too_large(self):
        """Oversized dimensions fail validation."""
        target = ProjectionTarget(
            name="huge",
            description="Huge",
            target_type=TargetType.PLANAR,
            width_m=150.0,
            height_m=1.0,
        )
        builder = PlanarTargetBuilder(target)
        errors = builder.validate_dimensions()
        assert any("100m" in e for e in errors)

    def test_full_validation(self, builder):
        """Full validation works."""
        is_valid, errors = builder.validate()
        assert is_valid
        assert len(errors) == 0

    def test_full_validation_surface_errors(self):
        """Surface errors are caught in validation."""
        target = ProjectionTarget(
            name="bad_surface",
            description="Bad surface",
            target_type=TargetType.PLANAR,
            surfaces=[
                ProjectionSurface(
                    name="bad",
                    surface_type=TargetType.PLANAR,
                    albedo=1.5,  # Invalid
                )
            ],
        )
        builder = PlanarTargetBuilder(target)
        is_valid, errors = builder.validate()
        assert not is_valid
        assert any("albedo" in e.lower() for e in errors)

    def test_get_calibration_points(self, builder):
        """Calibration points are computed correctly."""
        points = builder.get_calibration_points()

        assert len(points) == 3  # 3-point calibration
        # Points should be at corners
        # For 2.0 x 1.5m: corners at (-1, 0, -0.75), (1, 0, -0.75), (-1, 0, 0.75)

    def test_get_recommended_projector_position(self, builder):
        """Projector position is calculated correctly."""
        position, rotation = builder.get_recommended_projector_position(throw_ratio=1.5)

        # Distance = throw_ratio * width = 1.5 * 2.0 = 3.0
        assert position[0] == 0.0  # Centered on X
        assert position[1] == -3.0  # In front (negative Y)
        assert position[2] == 0.75  # Height = 1.5 / 2

        # Rotation should point forward
        assert rotation[0] == pytest.approx(math.pi / 2)

    def test_create_geometry_without_blender(self, builder):
        """Geometry creation handles missing Blender gracefully."""
        result = builder.create_geometry()

        # On systems without Blender, should have error
        if result.errors:
            assert any("Blender" in e or "bpy" in e for e in result.errors)
        else:
            # If Blender is available, should succeed
            assert result.success

    def test_create_geometry_with_invalid_config(self):
        """Invalid config produces error result."""
        target = ProjectionTarget(
            name="invalid",
            description="Invalid",
            target_type=TargetType.PLANAR,
            width_m=-1.0,
            height_m=0.0,
        )
        builder = PlanarTargetBuilder(target)
        result = builder.create_geometry()

        assert not result.success
        assert len(result.errors) > 0


class TestMultiSurfaceTargetBuilder:
    """Tests for MultiSurfaceTargetBuilder."""

    @pytest.fixture
    def multi_target(self):
        """Create a multi-surface target."""
        return ProjectionTarget(
            name="test_multi",
            description="Test multi-surface",
            target_type=TargetType.MULTI_SURFACE,
            surfaces=[
                ProjectionSurface(
                    name="upper",
                    surface_type=TargetType.PLANAR,
                    position=(0, 0, 1.5),
                    dimensions=(2.0, 0.8),
                    area_m2=1.6,
                ),
                ProjectionSurface(
                    name="lower",
                    surface_type=TargetType.PLANAR,
                    position=(0, 0, 0.3),
                    dimensions=(2.0, 0.6),
                    area_m2=1.2,
                ),
            ],
            width_m=2.0,
            height_m=2.0,
        )

    @pytest.fixture
    def builder(self, multi_target):
        """Create builder for multi-surface target."""
        return MultiSurfaceTargetBuilder(multi_target)

    def test_builder_initialization(self, builder, multi_target):
        """Builder initializes correctly."""
        assert builder.config == multi_target

    def test_get_calibration_points(self, builder):
        """Calibration points from multiple surfaces."""
        points = builder.get_calibration_points()

        # Should return up to 4 points for DLT
        assert len(points) <= 4

    def test_get_calibration_points_from_surface(self):
        """Uses surface calibration points if available."""
        target = ProjectionTarget(
            name="with_points",
            description="With points",
            target_type=TargetType.MULTI_SURFACE,
            surfaces=[
                ProjectionSurface(
                    name="s1",
                    surface_type=TargetType.PLANAR,
                    calibration_points=[(0, 0, 0), (1, 0, 0)],
                ),
                ProjectionSurface(
                    name="s2",
                    surface_type=TargetType.PLANAR,
                    calibration_points=[(0, 1, 0), (1, 1, 0)],
                ),
            ],
        )
        builder = MultiSurfaceTargetBuilder(target)
        points = builder.get_calibration_points()

        assert len(points) == 4

    def test_get_recommended_projector_position(self, builder):
        """Projector position covers all surfaces."""
        position, rotation = builder.get_recommended_projector_position(throw_ratio=1.5)

        # Position should be centered on the combined bounding box
        assert position[0] == 0.0  # Centered X

        # Rotation points forward
        assert rotation[0] == pytest.approx(math.pi / 2)

    def test_create_geometry_without_surfaces(self):
        """Multi-surface without surfaces produces error."""
        target = ProjectionTarget(
            name="empty_multi",
            description="Empty multi",
            target_type=TargetType.MULTI_SURFACE,
            surfaces=[],
        )
        builder = MultiSurfaceTargetBuilder(target)
        result = builder.create_geometry()

        assert not result.success
        assert any("No surfaces" in e for e in result.errors)

    def test_create_geometry_without_blender(self, builder):
        """Geometry creation handles missing Blender gracefully."""
        result = builder.create_geometry()

        if result.errors:
            assert any("Blender" in e or "bpy" in e for e in result.errors)


class TestCreateBuilder:
    """Tests for create_builder factory function."""

    def test_create_planar_builder(self):
        """Creates PlanarTargetBuilder for planar type."""
        target = ProjectionTarget(
            name="planar",
            description="Planar",
            target_type=TargetType.PLANAR,
        )
        builder = create_builder(target)
        assert isinstance(builder, PlanarTargetBuilder)

    def test_create_multi_surface_builder(self):
        """Creates MultiSurfaceTargetBuilder for multi_surface type."""
        target = ProjectionTarget(
            name="multi",
            description="Multi",
            target_type=TargetType.MULTI_SURFACE,
            surfaces=[
                ProjectionSurface(name="s1", surface_type=TargetType.PLANAR),
            ],
        )
        builder = create_builder(target)
        assert isinstance(builder, MultiSurfaceTargetBuilder)

    def test_unknown_type_defaults_to_planar(self):
        """Unknown types default to PlanarTargetBuilder."""
        target = ProjectionTarget(
            name="curved",
            description="Curved",
            target_type=TargetType.CURVED,
        )
        builder = create_builder(target)
        assert isinstance(builder, PlanarTargetBuilder)


class TestBuilderWithPreset:
    """Tests using preset targets."""

    def test_planar_2x2m_builder(self):
        """Build from PLANAR_2X2M preset."""
        builder = PlanarTargetBuilder(PLANAR_2X2M)

        points = builder.get_calibration_points()
        assert len(points) == 3

        position, rotation = builder.get_recommended_projector_position(throw_ratio=1.0)
        # Distance = 1.0 * 2.0 = 2.0
        assert position[1] == -2.0

    def test_validate_preset(self):
        """Preset targets validate successfully."""
        builder = PlanarTargetBuilder(PLANAR_2X2M)
        is_valid, errors = builder.validate()
        assert is_valid
        assert len(errors) == 0

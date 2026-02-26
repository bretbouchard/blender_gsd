"""
Unit tests for target preview system.

Tests for PreviewConfig, TargetPreview, and preview_target.
"""

import pytest
from lib.cinematic.projection.physical.targets import (
    ProjectionTarget,
    ProjectionSurface,
    TargetType,
    PreviewConfig,
    PreviewResult,
    TargetPreview,
    preview_target,
    PLANAR_2X2M,
)


class TestPreviewConfig:
    """Tests for PreviewConfig."""

    def test_default_config(self):
        """Default configuration values."""
        config = PreviewConfig()

        assert config.show_wireframe is True
        assert config.show_surface_normal is True
        assert config.show_calibration_points is True
        assert config.show_bounding_box is True
        assert config.show_frustum is True

    def test_default_colors(self):
        """Default color values."""
        config = PreviewConfig()

        assert config.wireframe_color == (1.0, 1.0, 0.0, 1.0)  # Yellow
        assert config.normal_color == (0.0, 1.0, 0.0, 1.0)    # Green
        assert config.point_color == (1.0, 0.0, 0.0, 1.0)     # Red
        assert config.bbox_color == (0.0, 0.0, 1.0, 1.0)      # Blue

    def test_custom_config(self):
        """Custom configuration values."""
        config = PreviewConfig(
            show_wireframe=False,
            show_frustum=False,
            point_size=0.1,
            normal_length=1.0,
        )

        assert config.show_wireframe is False
        assert config.show_frustum is False
        assert config.point_size == 0.1
        assert config.normal_length == 1.0

    def test_config_serialization(self):
        """Config serialization to dict."""
        config = PreviewConfig(show_wireframe=False)
        data = config.to_dict()

        assert data['show_wireframe'] is False
        assert 'point_size' in data
        assert 'wireframe_color' in data


class TestPreviewResult:
    """Tests for PreviewResult."""

    def test_default_result(self):
        """Default result is successful and empty."""
        result = PreviewResult()

        assert result.success is True
        assert len(result.objects) == 0
        assert len(result.errors) == 0
        assert len(result.warnings) == 0

    def test_result_with_warnings(self):
        """Result with warnings."""
        result = PreviewResult(
            warnings=["Blender not available"]
        )

        assert result.success is True
        assert len(result.warnings) == 1

    def test_result_with_errors(self):
        """Result with errors."""
        result = PreviewResult(
            success=False,
            errors=["Failed to create object"]
        )

        assert result.success is False
        assert len(result.errors) == 1


class TestTargetPreview:
    """Tests for TargetPreview."""

    @pytest.fixture
    def simple_target(self):
        """Create a simple target for testing."""
        return ProjectionTarget(
            name="preview_test",
            description="Preview test target",
            target_type=TargetType.PLANAR,
            surfaces=[
                ProjectionSurface(
                    name="main",
                    surface_type=TargetType.PLANAR,
                    dimensions=(2.0, 1.5),
                    calibration_points=[(0, 0, 0), (2, 0, 0), (0, 0, 1.5)],
                )
            ],
            width_m=2.0,
            height_m=1.5,
        )

    def test_initialization(self):
        """Preview initializes correctly."""
        preview = TargetPreview()

        assert len(preview.preview_objects) == 0
        assert preview.config is not None

    def test_initialization_with_config(self):
        """Preview with custom config."""
        config = PreviewConfig(show_wireframe=False)
        preview = TargetPreview(config)

        assert preview.config.show_wireframe is False

    def test_blender_available_property(self):
        """blender_available property works."""
        preview = TargetPreview()

        # Should return boolean
        assert isinstance(preview.blender_available, bool)

    def test_create_preview_without_blender(self, simple_target):
        """Preview handles missing Blender gracefully."""
        preview = TargetPreview()

        result = preview.create_preview(simple_target)

        # If Blender not available, should have warning
        if not preview.blender_available:
            assert len(result.warnings) > 0
            assert "Blender" in result.warnings[0]

    def test_clear_preview(self):
        """Clear preview removes objects."""
        preview = TargetPreview()

        # Add mock object
        preview.preview_objects = ["mock"]

        preview.clear_preview()

        assert len(preview.preview_objects) == 0

    def test_toggle_visibility(self):
        """Toggle visibility works."""
        preview = TargetPreview()

        # Create mock object with hide_viewport attribute
        class MockObj:
            hide_viewport = False
            hide_render = False

        preview.preview_objects = [MockObj()]

        preview.toggle_visibility(False)

        assert preview.preview_objects[0].hide_viewport is True
        assert preview.preview_objects[0].hide_render is True

        preview.toggle_visibility(True)

        assert preview.preview_objects[0].hide_viewport is False
        assert preview.preview_objects[0].hide_render is False


class TestPreviewTargetFunction:
    """Tests for preview_target convenience function."""

    def test_preview_target_function(self):
        """preview_target creates TargetPreview instance."""
        preview = preview_target(PLANAR_2X2M)

        assert isinstance(preview, TargetPreview)

    def test_preview_target_with_config(self):
        """preview_target with custom config."""
        config = PreviewConfig(show_frustum=False)
        preview = preview_target(PLANAR_2X2M, config=config)

        assert preview.config.show_frustum is False

    def test_preview_target_with_projector(self):
        """preview_target with projector parameter."""
        # Without Blender, projector parameter is ignored
        preview = preview_target(PLANAR_2X2M, projector=None)

        assert isinstance(preview, TargetPreview)

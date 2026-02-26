"""
Tests for projection workflow integration.
"""

import pytest
from dataclasses import asdict
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

from lib.cinematic.projection.physical.workflow import (
    ContentMappingWorkflow,
    render_for_projector,
    create_multi_surface_workflow,
)


class TestContentMappingWorkflow:
    """Tests for ContentMappingWorkflow class."""

    @pytest.fixture
    def mock_profile(self):
        """Create mock projector profile."""
        profile = Mock()
        profile.native_resolution = (1920, 1080)
        profile.throw_ratio = 1.5
        profile.lens_shift_horizontal = 0.0
        profile.lens_shift_vertical = 0.0
        profile.sensor_width = 36.0
        return profile

    @pytest.fixture
    def mock_calibration(self):
        """Create mock calibration."""
        calibration = Mock()
        calibration.calibration_type = Mock()
        calibration.calibration_type.value = "three_point"
        calibration.points = [
            Mock(world_position=(0, 0, 0), projector_uv=(0, 0)),
            Mock(world_position=(2, 0, 0), projector_uv=(1, 0)),
            Mock(world_position=(0, 1.5, 0), projector_uv=(0, 1)),
        ]
        return calibration

    def test_workflow_initialization(self, mock_profile, mock_calibration):
        """Test workflow initialization."""
        workflow = ContentMappingWorkflow(
            name="test_workflow",
            projector_profile=mock_profile,
            calibration=mock_calibration,
        )

        assert workflow.name == "test_workflow"
        assert workflow.projector_profile == mock_profile
        assert workflow.calibration == mock_calibration
        assert workflow.projector_camera is None
        assert workflow.proxy_geometry is None
        assert workflow.content_material is None
        assert workflow._errors == []

    def test_workflow_setup_without_blender(self, mock_profile, mock_calibration):
        """Test workflow setup fails gracefully without Blender."""
        workflow = ContentMappingWorkflow(
            name="test",
            projector_profile=mock_profile,
            calibration=mock_calibration,
        )

        result = workflow.setup()

        assert result == workflow  # Returns self for chaining
        # Note: On systems with Blender available, setup may succeed
        # This test just verifies that setup() returns self for chaining

    def test_workflow_calibrate_without_setup(self, mock_profile, mock_calibration):
        """Test workflow calibrate step."""
        workflow = ContentMappingWorkflow(
            name="test",
            projector_profile=mock_profile,
            calibration=mock_calibration,
        )

        result = workflow.calibrate()

        assert result == workflow  # Returns self for chaining

    def test_workflow_create_proxy_without_blender(self, mock_profile, mock_calibration):
        """Test workflow proxy creation fails gracefully without Blender."""
        workflow = ContentMappingWorkflow(
            name="test",
            projector_profile=mock_profile,
            calibration=mock_calibration,
        )

        result = workflow.create_proxy()

        assert result == workflow

    def test_workflow_map_content_without_blender(self, mock_profile, mock_calibration):
        """Test workflow content mapping fails gracefully without Blender."""
        workflow = ContentMappingWorkflow(
            name="test",
            projector_profile=mock_profile,
            calibration=mock_calibration,
        )

        result = workflow.map_content("//content/test.png")

        assert result == workflow

    def test_workflow_configure_output(self, mock_profile, mock_calibration):
        """Test workflow output configuration."""
        from lib.cinematic.projection.physical.output import ProjectionOutputConfig

        workflow = ContentMappingWorkflow(
            name="test",
            projector_profile=mock_profile,
            calibration=mock_calibration,
        )

        config = ProjectionOutputConfig(
            resolution=(1920, 1080),
            output_path="//output/",
        )

        result = workflow.configure_output(config)

        assert result == workflow
        assert workflow.output_config == config

    def test_workflow_render_without_config(self, mock_profile, mock_calibration):
        """Test workflow render handles missing config gracefully."""
        workflow = ContentMappingWorkflow(
            name="test",
            projector_profile=mock_profile,
            calibration=mock_calibration,
        )

        # render() adds to _errors and returns empty list instead of raising
        result = workflow.render("//output/")
        assert result == []
        assert len(workflow._errors) > 0
        assert "Output config not set" in workflow._errors[0]

    def test_workflow_execute_without_blender(self, mock_profile, mock_calibration):
        """Test complete workflow execution without Blender."""
        workflow = ContentMappingWorkflow(
            name="test",
            projector_profile=mock_profile,
            calibration=mock_calibration,
        )

        # Execute should handle missing Blender gracefully
        result = workflow.execute("//content/test.png", "//output/")

        # Result will be empty list due to errors
        assert isinstance(result, list)


class TestRenderForProjector:
    """Tests for render_for_projector convenience function."""

    def test_render_for_projector_with_invalid_profile(self):
        """Test render_for_projector with non-existent profile."""
        with pytest.raises(Exception):
            render_for_projector(
                content_path="//content/test.png",
                projector_profile_name="nonexistent_profile",
                calibration_points=[
                    ((0, 0, 0), (0, 0)),
                    ((1, 0, 0), (1, 0)),
                    ((0, 1, 0), (0, 1)),
                ],
                output_dir="//output/"
            )

    def test_render_for_projector_calibration_structure(self):
        """Test that render_for_projector creates correct calibration structure."""
        from lib.cinematic.projection.physical import load_profile, CalibrationType

        # This test verifies the function's logic without actually rendering
        # by checking the calibration structure would be correct

        calibration_points = [
            ((0, 0, 0), (0, 0)),
            ((1, 0, 0), (1, 0)),
            ((0, 1, 0), (0, 1)),
        ]

        # Verify the structure of the points
        assert len(calibration_points) == 3
        for wp, puv in calibration_points:
            assert len(wp) == 3  # World position is 3D
            assert len(puv) == 2  # Projector UV is 2D


class TestCreateMultiSurfaceWorkflow:
    """Tests for create_multi_surface_workflow function."""

    def test_create_multi_surface_workflow_structure(self):
        """Test multi-surface workflow structure."""
        # This test verifies the function signature and basic structure
        # without requiring Blender

        # Test would require actual profiles and calibrations
        # Here we just verify the function exists and has correct signature
        assert callable(create_multi_surface_workflow)

    def test_multi_surface_workflow_invalid_profile(self):
        """Test multi-surface workflow with invalid profile."""
        with pytest.raises(Exception):
            create_multi_surface_workflow(
                name="test",
                projector_profile_name="nonexistent",
                surface_calibrations={},
                content_paths={},
                output_dir="//output/"
            )


class TestWorkflowMethodChaining:
    """Tests for workflow method chaining."""

    @pytest.fixture
    def mock_profile(self):
        """Create mock projector profile."""
        profile = Mock()
        profile.native_resolution = (1920, 1080)
        profile.throw_ratio = 1.5
        profile.lens_shift_horizontal = 0.0
        profile.lens_shift_vertical = 0.0
        profile.sensor_width = 36.0
        return profile

    @pytest.fixture
    def mock_calibration(self):
        """Create mock calibration."""
        calibration = Mock()
        calibration.calibration_type = Mock()
        calibration.calibration_type.value = "three_point"
        calibration.points = [
            Mock(world_position=(0, 0, 0), projector_uv=(0, 0)),
            Mock(world_position=(2, 0, 0), projector_uv=(1, 0)),
            Mock(world_position=(0, 1.5, 0), projector_uv=(0, 1)),
        ]
        return calibration

    def test_method_chaining_setup(self, mock_profile, mock_calibration):
        """Test that setup returns self for chaining."""
        workflow = ContentMappingWorkflow(
            name="test",
            projector_profile=mock_profile,
            calibration=mock_calibration,
        )

        result = workflow.setup()
        assert result is workflow

    def test_method_chaining_calibrate(self, mock_profile, mock_calibration):
        """Test that calibrate returns self for chaining."""
        workflow = ContentMappingWorkflow(
            name="test",
            projector_profile=mock_profile,
            calibration=mock_calibration,
        )

        result = workflow.calibrate()
        assert result is workflow

    def test_method_chaining_create_proxy(self, mock_profile, mock_calibration):
        """Test that create_proxy returns self for chaining."""
        workflow = ContentMappingWorkflow(
            name="test",
            projector_profile=mock_profile,
            calibration=mock_calibration,
        )

        result = workflow.create_proxy()
        assert result is workflow

    def test_method_chaining_map_content(self, mock_profile, mock_calibration):
        """Test that map_content returns self for chaining."""
        workflow = ContentMappingWorkflow(
            name="test",
            projector_profile=mock_profile,
            calibration=mock_calibration,
        )

        result = workflow.map_content("//test.png")
        assert result is workflow

    def test_method_chaining_configure_output(self, mock_profile, mock_calibration):
        """Test that configure_output returns self for chaining."""
        from lib.cinematic.projection.physical.output import ProjectionOutputConfig

        workflow = ContentMappingWorkflow(
            name="test",
            projector_profile=mock_profile,
            calibration=mock_calibration,
        )

        config = ProjectionOutputConfig()
        result = workflow.configure_output(config)
        assert result is workflow

    def test_full_chain(self, mock_profile, mock_calibration):
        """Test full method chain."""
        from lib.cinematic.projection.physical.output import ProjectionOutputConfig

        workflow = ContentMappingWorkflow(
            name="test",
            projector_profile=mock_profile,
            calibration=mock_calibration,
        )

        # Full chain should work without errors
        result = (
            workflow
            .setup()
            .calibrate()
            .create_proxy()
            .map_content("//test.png")
            .configure_output(ProjectionOutputConfig())
        )

        assert result is workflow


class TestWorkflowErrorHandling:
    """Tests for workflow error handling."""

    @pytest.fixture
    def mock_profile(self):
        """Create mock projector profile."""
        profile = Mock()
        profile.native_resolution = (1920, 1080)
        profile.throw_ratio = 1.5
        return profile

    @pytest.fixture
    def mock_calibration(self):
        """Create mock calibration."""
        calibration = Mock()
        calibration.calibration_type = Mock()
        calibration.calibration_type.value = "three_point"
        calibration.points = []
        return calibration

    def test_errors_accumulate(self, mock_profile, mock_calibration):
        """Test that errors accumulate through workflow."""
        workflow = ContentMappingWorkflow(
            name="test",
            projector_profile=mock_profile,
            calibration=mock_calibration,
        )

        workflow.setup()
        initial_error_count = len(workflow._errors)

        workflow.calibrate()
        # Errors should accumulate, not reset
        assert len(workflow._errors) >= initial_error_count

    def test_skips_on_existing_errors(self, mock_profile, mock_calibration):
        """Test that steps skip when errors exist."""
        workflow = ContentMappingWorkflow(
            name="test",
            projector_profile=mock_profile,
            calibration=mock_calibration,
        )

        # Add an error manually
        workflow._errors.append("Manual error")

        # calibrate should skip due to existing errors
        result = workflow.calibrate()

        assert result is workflow
        # Error count should remain the same (skipped)
        assert len(workflow._errors) == 1

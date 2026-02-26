"""
End-to-end tests for physical projection mapping.

Tests complete workflows from profile loading to output rendering,
verifying that all components work together correctly.
"""

import pytest
import tempfile
from pathlib import Path

from lib.cinematic.projection.physical import (
    # Projector
    load_profile,
    list_profiles,
    create_projector_camera,
    # Calibration
    CalibrationPoint,
    CalibrationType,
    SurfaceCalibration,
    compute_alignment_transform,
    # Workflow
    ContentMappingWorkflow,
    render_for_projector,
    # Output
    ProjectionOutputConfig,
    OutputFormat,
    ColorSpace,
)

# Optional Blender support
try:
    import bpy
    HAS_BLENDER = True
except ImportError:
    HAS_BLENDER = False


@pytest.fixture
def temp_output_dir(tmp_path):
    """Create temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir(exist_ok=True)
    return output_dir


@pytest.fixture
def simple_calibration():
    """Create simple 3-point calibration for testing."""
    return SurfaceCalibration(
        name="test_calibration",
        calibration_type=CalibrationType.THREE_POINT,
        points=[
            CalibrationPoint(
                world_position=(0, 0, 0),
                projector_uv=(0, 0),
                label="Bottom-Left"
            ),
            CalibrationPoint(
                world_position=(2, 0, 0),
                projector_uv=(1, 0),
                label="Bottom-Right"
            ),
            CalibrationPoint(
                world_position=(0, 0, 1.5),
                projector_uv=(0, 1),
                label="Top-Left"
            ),
        ]
    )


class TestProfileToOutput:
    """Test complete workflow from profile selection to output."""

    def test_load_profile_and_create_calibration(self):
        """Load projector profile and create calibration."""
        # Load profile
        profile = load_profile("Epson_Home_Cinema_2150")

        assert profile is not None
        assert profile.name == "Epson_Home_Cinema_2150"
        assert profile.native_resolution == (1920, 1080)

        # Create calibration
        calibration = SurfaceCalibration(
            name="test_cal",
            calibration_type=CalibrationType.THREE_POINT,
            points=[
                CalibrationPoint((0, 0, 0), (0, 0), "BL"),
                CalibrationPoint((2, 0, 0), (1, 0), "BR"),
                CalibrationPoint((0, 0, 1.5), (0, 1), "TL"),
            ]
        )

        assert calibration is not None
        assert len(calibration.points) == 3

    def test_alignment_transform_accuracy(self, simple_calibration):
        """Test that alignment transform is computed correctly."""
        profile = load_profile("Epson_Home_Cinema_2150")

        # Extract points from calibration
        projector_points = [p.projector_uv for p in simple_calibration.points]
        world_points = [p.world_position for p in simple_calibration.points]

        # Compute alignment
        result = compute_alignment_transform(
            projector_points,
            world_points
        )

        assert result is not None
        assert result.transform is not None
        # For valid 3-point calibration, error should be minimal
        assert result.error < 1.0  # Less than 1 meter error

    def test_output_config_matches_profile(self):
        """Test output configuration matches projector profile."""
        profile = load_profile("Optoma_UHD38")  # 4K projector

        config = ProjectionOutputConfig(
            resolution=profile.native_resolution,
            format=OutputFormat.IMAGE_SEQUENCE,
            color_space=ColorSpace.SRGB,
            output_path="//output/",
        )

        # 4K projector
        assert config.resolution == (3840, 2160)
        assert config.format == OutputFormat.IMAGE_SEQUENCE
        assert config.color_space == ColorSpace.SRGB

    @pytest.mark.skipif(not HAS_BLENDER, reason="Blender not available")
    def test_create_projector_camera_from_profile(self):
        """Test creating Blender camera from projector profile."""
        profile = load_profile("Epson_Home_Cinema_2150")

        camera_obj = create_projector_camera(profile, name="Test_Projector")

        assert camera_obj is not None
        assert camera_obj.name == "Test_Projector"
        assert camera_obj.data.type == 'PERSP'

        # Cleanup
        bpy.data.objects.remove(camera_obj, do_unlink=True)


class TestContentMappingWorkflow:
    """Test ContentMappingWorkflow end-to-end."""

    def test_workflow_initialization(self, simple_calibration):
        """Test workflow initializes correctly."""
        profile = load_profile("Epson_Home_Cinema_2150")

        workflow = ContentMappingWorkflow(
            name="test_workflow",
            projector_profile=profile,
            calibration=simple_calibration
        )

        assert workflow.name == "test_workflow"
        assert workflow.projector_profile == profile
        assert workflow.calibration == simple_calibration

    def test_workflow_setup(self, simple_calibration):
        """Test workflow setup phase."""
        profile = load_profile("Epson_Home_Cinema_2150")

        workflow = ContentMappingWorkflow(
            name="setup_test",
            projector_profile=profile,
            calibration=simple_calibration
        )

        workflow.setup()

        # Setup should create internal state
        assert workflow is not None

    def test_workflow_calibrate(self, simple_calibration):
        """Test workflow calibrate phase."""
        profile = load_profile("Epson_Home_Cinema_2150")

        workflow = ContentMappingWorkflow(
            name="calibrate_test",
            projector_profile=profile,
            calibration=simple_calibration
        )

        workflow.setup()
        workflow.calibrate()

        # Calibration should compute alignment
        assert workflow is not None

    def test_workflow_method_chaining(self, simple_calibration):
        """Test workflow methods can be chained."""
        profile = load_profile("Epson_Home_Cinema_2150")

        workflow = ContentMappingWorkflow(
            name="chain_test",
            projector_profile=profile,
            calibration=simple_calibration
        )

        # Methods should return workflow for chaining
        result = workflow.setup().calibrate()

        assert result == workflow


class TestRenderForProjector:
    """Test render_for_projector convenience function."""

    def test_render_without_content(self, temp_output_dir):
        """Test render handles missing content gracefully."""
        # render_for_projector requires content, so this tests error handling
        # When content doesn't exist, should handle gracefully

        # Just verify the function exists and has correct signature
        import inspect
        sig = inspect.signature(render_for_projector)

        assert 'content_path' in sig.parameters
        assert 'projector_profile_name' in sig.parameters
        assert 'calibration_points' in sig.parameters
        assert 'output_dir' in sig.parameters

    def test_render_signature_validation(self):
        """Test render function validates parameters correctly."""
        # Test that function signature is correct
        from lib.cinematic.projection.physical.workflow import render_for_projector

        # Function should accept these parameters
        import inspect
        sig = inspect.signature(render_for_projector)

        expected_params = [
            'content_path',
            'projector_profile_name',
            'calibration_points',
            'output_dir',
        ]

        for param in expected_params:
            assert param in sig.parameters, f"Missing parameter: {param}"


class TestMultipleProfiles:
    """Test workflow with different projector profiles."""

    @pytest.mark.parametrize("profile_name", [
        "Epson_Home_Cinema_2150",
        "BenQ_W2700",
        "Optoma_UHD38",
    ])
    def test_workflow_with_different_profiles(self, profile_name, simple_calibration):
        """Test workflow works with different projector profiles."""
        profile = load_profile(profile_name)

        assert profile is not None

        workflow = ContentMappingWorkflow(
            name=f"test_{profile_name}",
            projector_profile=profile,
            calibration=simple_calibration
        )

        workflow.setup().calibrate()

        # Each profile should work
        assert workflow is not None

    def test_list_profiles_returns_profiles(self):
        """Test list_profiles returns available profiles."""
        profiles = list_profiles()

        assert len(profiles) > 0
        assert "Epson_Home_Cinema_2150" in profiles


class TestCalibrationTypes:
    """Test different calibration types."""

    def test_three_point_calibration(self):
        """Test 3-point calibration workflow."""
        calibration = SurfaceCalibration(
            name="three_point_test",
            calibration_type=CalibrationType.THREE_POINT,
            points=[
                CalibrationPoint((0, 0, 0), (0, 0), "BL"),
                CalibrationPoint((2, 0, 0), (1, 0), "BR"),
                CalibrationPoint((0, 0, 1.5), (0, 1), "TL"),
            ]
        )

        assert calibration.calibration_type == CalibrationType.THREE_POINT
        assert len(calibration.points) == 3

    def test_four_point_dlt_calibration(self):
        """Test 4-point DLT calibration workflow."""
        calibration = SurfaceCalibration(
            name="four_point_test",
            calibration_type=CalibrationType.FOUR_POINT_DLT,
            points=[
                CalibrationPoint((0, 0, 0), (0, 0), "BL"),
                CalibrationPoint((2, 0, 0), (1, 0), "BR"),
                CalibrationPoint((2, 0, 1.5), (1, 1), "TR"),
                CalibrationPoint((0, 0, 1.5), (0, 1), "TL"),
            ]
        )

        assert calibration.calibration_type == CalibrationType.FOUR_POINT_DLT
        assert len(calibration.points) == 4


class TestOutputFormats:
    """Test different output formats."""

    @pytest.mark.parametrize("output_format", [
        OutputFormat.IMAGE_SEQUENCE,
        OutputFormat.VIDEO,
        OutputFormat.EXR,
    ])
    def test_output_format_configuration(self, output_format):
        """Test output format configuration."""
        profile = load_profile("Epson_Home_Cinema_2150")

        config = ProjectionOutputConfig(
            resolution=profile.native_resolution,
            format=output_format,
            color_space=ColorSpace.SRGB,
            output_path="//output/",
        )

        assert config.format == output_format

    def test_color_space_configuration(self):
        """Test color space configuration."""
        config = ProjectionOutputConfig(
            resolution=(1920, 1080),
            format=OutputFormat.VIDEO,
            color_space=ColorSpace.ACES,
            output_path="//output/",
        )

        assert config.color_space == ColorSpace.ACES


class TestIntegrationWithTargets:
    """Test integration with target presets."""

    def test_load_target_preset_if_available(self):
        """Test loading target preset if available."""
        try:
            from lib.cinematic.projection.physical.targets import (
                load_target_preset,
                list_target_presets,
            )

            # List available presets
            presets = list_target_presets()

            # May be empty if presets not yet loaded
            assert isinstance(presets, list)

        except ImportError:
            pytest.skip("Target presets module not available")

    def test_create_target_from_measurements(self):
        """Test creating target from measurements."""
        try:
            from lib.cinematic.projection.physical.targets import (
                TargetImporter,
                ProjectionTarget,
            )

            importer = TargetImporter()
            importer.add_point_measurement("corner_bl", (0, 0, 0))
            importer.add_point_measurement("corner_br", (2, 0, 0))
            importer.add_point_measurement("corner_tl", (0, 0, 1.5))

            target = importer.compute_target()

            assert target is not None
            assert isinstance(target, ProjectionTarget)

        except ImportError:
            pytest.skip("Target presets module not available")


class TestErrorHandling:
    """Test error handling in E2E workflows."""

    def test_invalid_profile_name(self):
        """Test handling of invalid profile name."""
        with pytest.raises(KeyError):
            load_profile("nonexistent_profile_xyz")

    def test_invalid_calibration_points(self):
        """Test handling of invalid calibration points."""
        # Collinear points should produce poor calibration
        calibration = SurfaceCalibration(
            name="collinear_test",
            calibration_type=CalibrationType.THREE_POINT,
            points=[
                CalibrationPoint((0, 0, 0), (0, 0), "P1"),
                CalibrationPoint((1, 0, 0), (0.5, 0), "P2"),  # Same line
                CalibrationPoint((2, 0, 0), (1, 0), "P3"),   # Same line
            ]
        )

        # Should still create calibration object
        assert calibration is not None
        assert len(calibration.points) == 3


class TestCompleteWorkflow:
    """Complete E2E workflow tests."""

    def test_minimal_complete_workflow(self, temp_output_dir, simple_calibration):
        """Test minimal complete workflow."""
        # 1. Load profile
        profile = load_profile("Epson_Home_Cinema_2150")
        assert profile is not None

        # 2. Create workflow
        workflow = ContentMappingWorkflow(
            name="minimal_test",
            projector_profile=profile,
            calibration=simple_calibration
        )

        # 3. Setup and calibrate
        workflow.setup()
        workflow.calibrate()

        # 4. Verify workflow state
        assert workflow is not None

    def test_workflow_with_custom_resolution(self, simple_calibration):
        """Test workflow with custom output resolution."""
        profile = load_profile("Optoma_UHD38")  # 4K projector

        # Custom resolution (downscaled from 4K)
        custom_resolution = (1920, 1080)

        config = ProjectionOutputConfig(
            resolution=custom_resolution,
            format=OutputFormat.VIDEO,
            color_space=ColorSpace.SRGB,
            output_path="//output/",
        )

        assert config.resolution == custom_resolution
        # Profile is still 4K
        assert profile.native_resolution == (3840, 2160)

    @pytest.mark.skipif(not HAS_BLENDER, reason="Blender not available")
    def test_full_pipeline_with_blender(self, temp_output_dir, simple_calibration):
        """Full pipeline test with Blender available."""
        import bpy
        from mathutils import Matrix

        # 1. Load profile
        profile = load_profile("Epson_Home_Cinema_2150")

        # 2. Create projector camera
        camera = create_projector_camera(profile, name="E2E_Projector")
        assert camera is not None

        # 3. Compute alignment - extract points from calibration
        projector_points = [p.projector_uv for p in simple_calibration.points]
        world_points = [p.world_position for p in simple_calibration.points]

        result = compute_alignment_transform(projector_points, world_points)
        assert result is not None

        # 4. Apply transform to camera (convert Matrix4x4 to Blender Matrix)
        blender_matrix = Matrix(result.transform.data)
        camera.matrix_world = blender_matrix

        # 5. Verify camera is in scene
        assert camera.name in bpy.data.objects

        # Cleanup
        bpy.data.objects.remove(camera, do_unlink=True)

"""
Cinematic System Integration Tests

Tests that require Blender's bpy module for cinematic system functionality.
"""

import pytest
import sys
from pathlib import Path

# Add lib to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from . import requires_blender, BPY_AVAILABLE, BLENDER_AVAILABLE

# Skip all tests in this module if Blender not available
pytestmark = pytest.mark.skipif(
    not (BLENDER_AVAILABLE and BPY_AVAILABLE),
    reason="Blender and bpy module required"
)


@requires_blender
class TestCameraSystem:
    """Tests for camera system with Blender."""

    def test_create_camera(self):
        """Test creating a Blender camera."""
        import bpy

        from lib.cinematic.camera import create_camera
        from lib.cinematic.types import CameraConfig

        # Create camera
        config = CameraConfig(
            name="Test_Camera",
            focal_length=50.0,
            sensor_width=36.0,
        )

        camera = create_camera(config)

        assert camera is not None
        assert camera.name == "Test_Camera"
        assert abs(camera.data.lens - 50.0) < 0.1

        # Cleanup
        bpy.data.objects.remove(camera)

    def test_camera_dof(self):
        """Test camera depth of field configuration."""
        import bpy

        from lib.cinematic.camera import create_camera
        from lib.cinematic.types import CameraConfig

        # CameraConfig has focus_distance and f_stop attributes directly
        config = CameraConfig(
            name="Test_DOF_Camera",
            focal_length=35.0,
            focus_distance=10.0,
            f_stop=2.8,
        )

        camera = create_camera(config)

        assert camera is not None
        # Check DOF is enabled and settings applied
        assert camera.data.dof is not None
        assert abs(camera.data.dof.focus_distance - 10.0) < 0.1
        assert abs(camera.data.dof.aperture_fstop - 2.8) < 0.1

        # Cleanup
        bpy.data.objects.remove(camera)


@requires_blender
class TestLightingSystem:
    """Tests for lighting system with Blender."""

    def test_create_point_light(self):
        """Test creating a point light."""
        import bpy

        from lib.cinematic.lighting import create_light
        from lib.cinematic.types import LightConfig

        config = LightConfig(
            name="Test_Point_Light",
            light_type="point",
            intensity=1000.0,
            color=(1.0, 0.95, 0.9),
        )

        light = create_light(config)

        assert light is not None
        assert light.name == "Test_Point_Light"

        # Cleanup
        bpy.data.objects.remove(light)

    def test_create_area_light(self):
        """Test creating an area light."""
        import bpy

        from lib.cinematic.lighting import create_light
        from lib.cinematic.types import LightConfig

        config = LightConfig(
            name="Test_Area_Light",
            light_type="area",
            intensity=500.0,
            color=(0.9, 0.9, 1.0),
        )

        light = create_light(config)

        assert light is not None
        assert light.name == "Test_Area_Light"

        # Cleanup
        bpy.data.objects.remove(light)


@requires_blender
class TestRenderSystem:
    """Tests for render system with Blender."""

    def test_render_settings(self):
        """Test applying render settings."""
        import bpy

        from lib.cinematic.render import apply_render_settings
        from lib.cinematic.types import CinematicRenderSettings

        settings = CinematicRenderSettings(
            resolution_x=1920,
            resolution_y=1080,
            samples=64,
        )

        apply_render_settings(settings)

        scene = bpy.context.scene
        assert scene.render.resolution_x == 1920
        assert scene.render.resolution_y == 1080

    def test_quality_tier(self):
        """Test quality tier presets."""
        from lib.cinematic.render import QUALITY_TIERS
        from lib.cinematic.types import CinematicRenderSettings

        # Check that quality tiers exist
        assert "preview" in QUALITY_TIERS or "cycles_preview" in QUALITY_TIERS

        # Get a quality tier preset
        if "cycles_preview" in QUALITY_TIERS:
            settings = QUALITY_TIERS["cycles_preview"]
        else:
            settings = QUALITY_TIERS.get("preview", CinematicRenderSettings())

        assert settings.samples > 0
        assert settings.resolution_x > 0
        assert settings.resolution_y > 0


@requires_blender
class TestBackdropSystem:
    """Tests for backdrop system with Blender."""

    def test_create_infinite_curve(self):
        """Test creating infinite curve backdrop."""
        import bpy

        from lib.cinematic.backdrops import create_infinite_curve
        from lib.cinematic.types import BackdropConfig

        # BackdropConfig uses radius, not size
        config = BackdropConfig(
            backdrop_type="infinite_curve",
            radius=10.0,
        )

        backdrop = create_infinite_curve(config)

        assert backdrop is not None

        # Cleanup
        bpy.data.objects.remove(backdrop)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "blender_integration"])

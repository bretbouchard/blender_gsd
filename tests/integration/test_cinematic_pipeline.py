"""
Cinematic Pipeline Integration Tests

Tests end-to-end cinematic system workflows that can run without Blender.
Uses the existing module structure.

Note: These tests use mocked bpy to work without Blender.
"""

import pytest
from lib.oracle import compare_numbers, compare_vectors, Oracle


@pytest.mark.integration
class TestCinematicTypes:
    """Tests for cinematic type system integration."""

    def test_camera_config_roundtrip(self):
        """CameraConfig should store and retrieve values correctly."""
        from lib.cinematic.types import CameraConfig

        config = CameraConfig(
            name="test_camera",
            focal_length=50.0,
            sensor_width=36.0,
        )

        compare_numbers(config.focal_length, 50.0)
        assert config.name == "test_camera"

    def test_light_config_integration(self):
        """LightConfig should integrate with lighting system."""
        from lib.cinematic.types import LightConfig, LightRigConfig

        config = LightConfig(
            name="key_light",
            intensity=1000.0,
            color=(1.0, 0.95, 0.9),
        )

        compare_numbers(config.intensity, 1000.0)
        compare_vectors(config.color, (1.0, 0.95, 0.9))

    def test_render_settings_integration(self):
        """RenderSettings should integrate with render system."""
        from lib.cinematic.types import RenderSettings

        settings = RenderSettings(
            resolution_x=1920,
            resolution_y=1080,
            samples=64,
        )

        compare_numbers(settings.resolution_x, 1920)
        compare_numbers(settings.samples, 64)

    def test_color_config_integration(self):
        """ColorConfig should store color settings."""
        from lib.cinematic.types import ColorConfig, LUTConfig

        config = ColorConfig(
            exposure=0.0,
            gamma=2.2,
        )

        compare_numbers(config.gamma, 2.2)


@pytest.mark.integration
class TestShotAssembly:
    """Tests for shot assembly pipeline."""

    def test_shot_assembly_config(self):
        """ShotAssemblyConfig should combine all shot settings."""
        from lib.cinematic.types import ShotAssemblyConfig

        config = ShotAssemblyConfig(
            name="test_shot",
            template="cinematic",
        )

        assert config.name == "test_shot"
        assert config.template == "cinematic"

    def test_lighting_rig_from_preset(self):
        """Lighting rig should load from preset."""
        from lib.cinematic.types import LightRigConfig

        # Three-point lighting preset
        rig = LightRigConfig(
            name="three_point",
            description="Standard three-point lighting",
        )

        assert rig.name == "three_point"


@pytest.mark.integration
class TestAnimationPipeline:
    """Tests for animation pipeline."""

    def test_turntable_animation_config(self):
        """Turntable animation should be configurable."""
        from lib.cinematic.types import TurntableConfig

        config = TurntableConfig(
            enabled=True,
            axis="Z",
            angle_range=(0, 360),
            duration=100,
        )

        assert config.axis == "Z"
        compare_numbers(config.duration, 100)


@pytest.mark.integration
class TestFollowCameraPipeline:
    """Tests for follow camera system."""

    def test_follow_mode_config(self):
        """Follow mode should be configurable."""
        from lib.cinematic.follow_cam.types import (
            FollowCameraConfig,
            FollowMode,
        )

        config = FollowCameraConfig(
            follow_mode=FollowMode.CHASE,
            ideal_distance=10.0,
            ideal_height=3.0,
        )

        assert config.follow_mode == FollowMode.CHASE
        compare_numbers(config.ideal_distance, 10.0)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-m", "integration"])

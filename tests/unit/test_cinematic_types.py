"""
Cinematic Types Unit Tests

Tests for: lib/cinematic/types.py
Coverage target: 85%+
"""

import pytest
from lib.oracle import compare_numbers, compare_vectors, compare_within_range

from lib.cinematic.types import (
    Transform3D,
    CameraConfig,
    LightConfig,
    GelConfig,
    HDRIConfig,
    LightRigConfig,
    BackdropConfig,
    RenderSettings,
    ShotState,
    PlumbBobConfig,
    RigConfig,
    ImperfectionConfig,
    MultiCameraLayout,
    ColorConfig,
    LUTConfig,
    ExposureLockConfig,
    AnimationConfig,
    MotionPathConfig,
    TurntableConfig,
    CinematicRenderSettings,
    ShuffleConfig,
    FrameState,
    DepthLayerConfig,
    CompositionGuide,
    LensFXConfig,
    CompositionConfig,
    CompleteShotConfig,
    SHOT_SIZES,
    LENS_BY_SHOT_SIZE,
    FSTOP_BY_SHOT_SIZE,
    CAMERA_ANGLES,
    CAMERA_POSITIONS,
    LIGHTING_RATIOS,
)


class TestTransform3D:
    """Unit tests for Transform3D dataclass."""

    def test_default_values(self):
        """Default transform should be origin with no rotation."""
        t = Transform3D()
        compare_vectors(t.position, (0.0, 0.0, 0.0))
        compare_vectors(t.rotation, (0.0, 0.0, 0.0))
        compare_vectors(t.scale, (1.0, 1.0, 1.0))

    def test_custom_values(self):
        """Custom values should be stored correctly."""
        t = Transform3D(
            position=(1.0, 2.0, 3.0),
            rotation=(45.0, 0.0, 90.0),
            scale=(2.0, 2.0, 2.0),
        )
        compare_vectors(t.position, (1.0, 2.0, 3.0))
        compare_vectors(t.rotation, (45.0, 0.0, 90.0))
        compare_vectors(t.scale, (2.0, 2.0, 2.0))

    def test_to_blender(self):
        """to_blender should convert rotation to radians."""
        t = Transform3D(position=(1, 2, 3), rotation=(90, 0, 0), scale=(1, 1, 1))
        result = t.to_blender()

        assert result["location"] == [1, 2, 3]
        assert result["scale"] == [1, 1, 1]

        # 90 degrees should be approximately 1.5708 radians
        compare_numbers(result["rotation_euler"][0], 1.5708, tolerance=0.01)

    def test_to_dict_and_from_dict(self):
        """Serialization round-trip should preserve values."""
        original = Transform3D(position=(5, -3, 2), rotation=(10, 20, 30))

        data = original.to_dict()
        restored = Transform3D.from_dict(data)

        compare_vectors(restored.position, original.position)
        compare_vectors(restored.rotation, original.rotation)
        compare_vectors(restored.scale, original.scale)


class TestCameraConfig:
    """Unit tests for CameraConfig dataclass."""

    def test_default_values(self):
        """Default camera should have sensible defaults."""
        cam = CameraConfig()

        assert cam.name == "hero_camera"
        compare_numbers(cam.focal_length, 50.0)
        compare_numbers(cam.f_stop, 4.0)
        compare_numbers(cam.sensor_width, 36.0)
        compare_numbers(cam.sensor_height, 24.0)

    def test_custom_values(self):
        """Custom camera values should be stored."""
        cam = CameraConfig(
            name="portrait_lens",
            focal_length=85.0,
            f_stop=1.8,
            focus_distance=2.0,
        )

        assert cam.name == "portrait_lens"
        compare_numbers(cam.focal_length, 85.0)
        compare_numbers(cam.f_stop, 1.8)
        compare_numbers(cam.focus_distance, 2.0)

    def test_to_params(self):
        """to_params should include transform as blender format."""
        cam = CameraConfig(
            name="test",
            focal_length=50.0,
            transform=Transform3D(position=(0, -5, 2)),
        )

        params = cam.to_params()

        assert params["name"] == "test"
        assert params["focal_length"] == 50.0
        assert "transform" in params
        assert params["transform"]["location"] == [0, -5, 2]

    def test_serialization_round_trip(self):
        """to_dict/from_dict should preserve all values."""
        original = CameraConfig(
            name="test_cam",
            focal_length=35.0,
            f_stop=2.8,
            transform=Transform3D(position=(1, 2, 3)),
        )

        data = original.to_dict()
        restored = CameraConfig.from_dict(data)

        assert restored.name == original.name
        compare_numbers(restored.focal_length, original.focal_length)
        compare_numbers(restored.f_stop, original.f_stop)
        compare_vectors(restored.transform.position, original.transform.position)


class TestLightConfig:
    """Unit tests for LightConfig dataclass."""

    def test_default_values(self):
        """Default light should be area light with white color."""
        light = LightConfig()

        assert light.name == "key_light"
        assert light.light_type == "area"
        compare_vectors(light.color, (1.0, 1.0, 1.0))
        compare_numbers(light.intensity, 1000.0)

    def test_spot_light_config(self):
        """Spot light should support spot-specific properties."""
        light = LightConfig(
            name="spot",
            light_type="spot",
            spot_size=0.5,
            spot_blend=0.3,
        )

        assert light.light_type == "spot"
        compare_numbers(light.spot_size, 0.5)
        compare_numbers(light.spot_blend, 0.3)

    def test_area_light_shapes(self):
        """Area light should support different shapes."""
        for shape in ["SQUARE", "RECTANGLE", "DISK", "ELLIPSE"]:
            light = LightConfig(shape=shape)
            assert light.shape == shape

    def test_color_temperature(self):
        """Light should support color temperature mode."""
        light = LightConfig(
            use_temperature=True,
            temperature=3200.0,  # Tungsten
        )

        assert light.use_temperature is True
        compare_numbers(light.temperature, 3200.0)


class TestPlumbBobConfig:
    """Unit tests for PlumbBobConfig dataclass."""

    def test_default_values(self):
        """Default plumb bob should be auto mode."""
        pb = PlumbBobConfig()

        assert pb.mode == "auto"
        compare_vectors(pb.offset, (0.0, 0.0, 0.0))
        assert pb.focus_mode == "auto"

    def test_manual_mode(self):
        """Manual mode should use explicit position."""
        pb = PlumbBobConfig(
            mode="manual",
            manual_position=(1.0, 2.0, 3.0),
        )

        assert pb.mode == "manual"
        compare_vectors(pb.manual_position, (1.0, 2.0, 3.0))

    def test_object_mode(self):
        """Object mode should reference another object."""
        pb = PlumbBobConfig(
            mode="object",
            target_object="Cube",
            offset=(0, 0, 0.5),
        )

        assert pb.mode == "object"
        assert pb.target_object == "Cube"
        compare_vectors(pb.offset, (0.0, 0.0, 0.5))


class TestRigConfig:
    """Unit tests for RigConfig dataclass."""

    def test_default_tripod(self):
        """Default rig should be tripod."""
        rig = RigConfig()

        assert rig.rig_type == "tripod"

    def test_rig_types(self):
        """All rig types should be valid."""
        valid_types = [
            "tripod", "tripod_orbit", "dolly", "dolly_curved",
            "crane", "steadicam", "drone"
        ]

        for rig_type in valid_types:
            rig = RigConfig(rig_type=rig_type)
            assert rig.rig_type == rig_type


class TestCompositionConfig:
    """Unit tests for CompositionConfig dataclass."""

    def test_default_values(self):
        """Default composition should be medium shot at eye level."""
        comp = CompositionConfig()

        assert comp.shot_size == "m"
        assert comp.camera_angle == "eye"
        assert comp.camera_position == "three_quarter"

    def test_from_shot_size(self):
        """from_shot_size should auto-select lens and f-stop."""
        # Close-up should get 85mm lens at f/2.8
        comp = CompositionConfig.from_shot_size("cu")

        assert comp.shot_size == "cu"
        compare_numbers(comp.lens_focal_length, 85.0)
        compare_numbers(comp.f_stop, 2.8)

    def test_from_shot_size_with_mood(self):
        """Mood should affect lighting ratio."""
        comp_dramatic = CompositionConfig.from_shot_size("m", mood="dramatic")
        comp_normal = CompositionConfig.from_shot_size("m", mood="normal")

        # Dramatic should have higher ratio (more contrast)
        assert comp_dramatic.lighting_ratio > comp_normal.lighting_ratio


class TestCompleteShotConfig:
    """Unit tests for CompleteShotConfig dataclass."""

    def test_default_values(self):
        """Default shot should have all nested configs."""
        shot = CompleteShotConfig()

        assert shot.name == "shot_01"
        assert isinstance(shot.composition, CompositionConfig)
        assert isinstance(shot.camera, CameraConfig)
        assert isinstance(shot.plumb_bob, PlumbBobConfig)

    def test_from_shot_size(self):
        """from_shot_size should create complete config from shot size."""
        shot = CompleteShotConfig.from_shot_size("cu", mood="dramatic")

        assert "cu" in shot.name
        assert shot.composition.shot_size == "cu"
        compare_numbers(shot.camera.focal_length, 85.0)
        compare_numbers(shot.camera.f_stop, 2.8)

    def test_serialization_round_trip(self):
        """to_dict/from_dict should preserve nested configs."""
        original = CompleteShotConfig(
            name="test_shot",
            composition=CompositionConfig(shot_size="mcu"),
            camera=CameraConfig(focal_length=65.0),
        )

        data = original.to_dict()
        restored = CompleteShotConfig.from_dict(data)

        assert restored.name == "test_shot"
        assert restored.composition.shot_size == "mcu"
        compare_numbers(restored.camera.focal_length, 65.0)


class TestShotState:
    """Unit tests for ShotState dataclass."""

    def test_default_values(self):
        """Default state should have shot_name and camera."""
        state = ShotState(shot_name="test_shot")

        assert state.shot_name == "test_shot"
        assert state.version == 1
        assert isinstance(state.camera, CameraConfig)

    def test_to_yaml_dict(self):
        """to_yaml_dict should produce serializable dict."""
        state = ShotState(
            shot_name="hero_01",
            version=2,
            camera=CameraConfig(focal_length=50.0),
        )

        data = state.to_yaml_dict()

        assert data["shot_name"] == "hero_01"
        assert data["version"] == 2
        assert "camera" in data
        assert "focal_length" in data["camera"]

    def test_from_yaml_dict(self):
        """from_yaml_dict should reconstruct state."""
        data = {
            "shot_name": "test",
            "version": 3,
            "camera": {
                "name": "main",
                "focal_length": 35.0,
            },
        }

        state = ShotState.from_yaml_dict(data)

        assert state.shot_name == "test"
        assert state.version == 3
        compare_numbers(state.camera.focal_length, 35.0)


class TestCinematographyConstants:
    """Tests for cinematography constants."""

    def test_shot_sizes_exist(self):
        """All shot sizes should be defined."""
        expected_sizes = ["ecu", "cu", "mcu", "m", "mf", "f", "w", "ew"]

        for size in expected_sizes:
            assert size in SHOT_SIZES
            assert "name" in SHOT_SIZES[size]
            assert "description" in SHOT_SIZES[size]

    def test_lens_by_shot_size(self):
        """Each shot size should have lens recommendation."""
        for size in SHOT_SIZES:
            assert size in LENS_BY_SHOT_SIZE
            assert "focal_length" in LENS_BY_SHOT_SIZE[size]
            assert "preset" in LENS_BY_SHOT_SIZE[size]

    def test_fstop_by_shot_size(self):
        """Each shot size should have f-stop recommendation."""
        for size in SHOT_SIZES:
            assert size in FSTOP_BY_SHOT_SIZE
            assert "f_stop" in FSTOP_BY_SHOT_SIZE[size]

    def test_camera_angles(self):
        """Camera angles should have power and emotion."""
        for angle_name, angle_data in CAMERA_ANGLES.items():
            assert "height_factor" in angle_data
            assert "power" in angle_data
            assert "emotion" in angle_data

    def test_lighting_ratios(self):
        """Lighting ratios should have key:fill values."""
        for ratio_name, ratio_data in LIGHTING_RATIOS.items():
            assert "key_fill" in ratio_data
            assert ratio_data["key_fill"] > 0


class TestAnimationConfig:
    """Unit tests for AnimationConfig dataclass."""

    def test_default_static(self):
        """Default animation should be static (no animation)."""
        anim = AnimationConfig()

        assert anim.enabled is False
        assert anim.type == "static"

    def test_orbit_config(self):
        """Orbit animation should have angle range and radius."""
        anim = AnimationConfig(
            enabled=True,
            type="orbit",
            angle_range=(0, 360),
            radius=2.0,
        )

        assert anim.enabled is True
        assert anim.type == "orbit"
        compare_vectors(anim.angle_range, (0.0, 360.0))
        compare_numbers(anim.radius, 2.0)

    def test_easing_options(self):
        """Animation should support various easing functions."""
        easing_types = ["linear", "ease_in", "ease_out", "ease_in_out"]

        for easing in easing_types:
            anim = AnimationConfig(easing=easing)
            assert anim.easing == easing


class TestBackdropConfig:
    """Unit tests for BackdropConfig dataclass."""

    def test_default_infinite_curve(self):
        """Default backdrop should be infinite curve."""
        backdrop = BackdropConfig()

        assert backdrop.backdrop_type == "infinite_curve"
        assert backdrop.shadow_catcher is True

    def test_gradient_backdrop(self):
        """Gradient backdrop should support color stops."""
        backdrop = BackdropConfig(
            backdrop_type="gradient",
            color_bottom=(0.1, 0.1, 0.1),
            color_top=(0.9, 0.9, 0.9),
        )

        assert backdrop.backdrop_type == "gradient"
        compare_vectors(backdrop.color_bottom, (0.1, 0.1, 0.1))
        compare_vectors(backdrop.color_top, (0.9, 0.9, 0.9))


class TestCinematicRenderSettings:
    """Unit tests for CinematicRenderSettings dataclass."""

    def test_default_preview(self):
        """Default settings should be preview quality."""
        settings = CinematicRenderSettings()

        assert settings.quality_tier == "preview"
        assert settings.engine == "BLENDER_EEVEE_NEXT"
        assert settings.resolution_x == 1920
        assert settings.resolution_y == 1080

    def test_pass_configuration(self):
        """Should support various render passes."""
        settings = CinematicRenderSettings(
            use_pass_z=True,
            use_pass_normal=True,
            use_pass_cryptomatte=True,
        )

        assert settings.use_pass_z is True
        assert settings.use_pass_normal is True
        assert settings.use_pass_cryptomatte is True


class TestShuffleConfig:
    """Unit tests for ShuffleConfig dataclass."""

    def test_default_disabled(self):
        """Shuffle should be disabled by default."""
        shuffle = ShuffleConfig()

        assert shuffle.enabled is False
        assert shuffle.num_variations == 5

    def test_variation_ranges(self):
        """Shuffle ranges should have min < max."""
        shuffle = ShuffleConfig(enabled=True)

        assert shuffle.camera_angle_range[0] < shuffle.camera_angle_range[1]
        assert shuffle.focal_length_range[0] < shuffle.focal_length_range[1]

    def test_seed_for_reproducibility(self):
        """Seed should enable reproducible variations."""
        shuffle = ShuffleConfig(seed=42)

        assert shuffle.seed == 42


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])

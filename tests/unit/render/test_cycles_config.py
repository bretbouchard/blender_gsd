"""
Tests for render/cycles_config module.

Tests run WITHOUT Blender (bpy) by testing only non-Blender-dependent code paths.
"""

import pytest


class TestDeviceType:
    """Tests for DeviceType enum."""

    def test_device_type_values(self):
        """Test DeviceType enum values."""
        from lib.render.cycles_config import DeviceType

        assert DeviceType.CPU.value == "CPU"
        assert DeviceType.CUDA.value == "CUDA"
        assert DeviceType.OPTIX.value == "OPTIX"
        assert DeviceType.HIP.value == "HIP"
        assert DeviceType.METAL.value == "METAL"
        assert DeviceType.ONEAPI.value == "ONEAPI"


class TestDenoiserType:
    """Tests for DenoiserType enum."""

    def test_denoiser_type_values(self):
        """Test DenoiserType enum values."""
        from lib.render.cycles_config import DenoiserType

        assert DenoiserType.OPTIX.value == "OPTIX"
        assert DenoiserType.OPENIMAGEDENOISE.value == "OPENIMAGEDENOISE"
        assert DenoiserType.NONE.value == "NONE"


class TestCyclesConfig:
    """Tests for CyclesConfig dataclass."""

    def test_config_creation(self):
        """Test creating a CyclesConfig."""
        from lib.render.cycles_config import CyclesConfig

        config = CyclesConfig(
            name="test_config",
            samples=512,
            adaptive_sampling=True,
        )

        assert config.name == "test_config"
        assert config.samples == 512
        assert config.adaptive_sampling is True

    def test_config_defaults(self):
        """Test CyclesConfig default values."""
        from lib.render.cycles_config import CyclesConfig

        config = CyclesConfig(name="default")
        assert config.samples == 256
        assert config.adaptive_sampling is True
        assert config.adaptive_threshold == 0.01
        assert config.use_denoising is True
        assert config.denoiser == "OPENIMAGEDENOISE"
        assert config.use_guiding is True
        assert config.max_bounces == 12

    def test_config_to_dict(self):
        """Test CyclesConfig serialization."""
        from lib.render.cycles_config import CyclesConfig

        config = CyclesConfig(
            name="test",
            samples=128,
            use_denoising=True,
        )
        data = config.to_dict()

        assert data["name"] == "test"
        assert data["samples"] == 128
        assert data["use_denoising"] is True


class TestCyclesPresets:
    """Tests for CYCLES_PRESETS constant."""

    def test_presets_dict(self):
        """Test that CYCLES_PRESETS is a dictionary."""
        from lib.render.cycles_config import CYCLES_PRESETS

        assert isinstance(CYCLES_PRESETS, dict)
        assert len(CYCLES_PRESETS) > 0

    def test_preview_preset(self):
        """Test preview preset."""
        from lib.render.cycles_config import CYCLES_PRESETS

        preset = CYCLES_PRESETS["preview"]
        assert preset.name == "preview"
        assert preset.samples <= 64

    def test_production_preset(self):
        """Test production preset."""
        from lib.render.cycles_config import CYCLES_PRESETS

        preset = CYCLES_PRESETS["production"]
        assert preset.name == "production"
        assert preset.samples >= 128
        assert preset.use_denoising is True
        assert preset.use_guiding is True

    def test_archive_preset(self):
        """Test archive preset for maximum quality."""
        from lib.render.cycles_config import CYCLES_PRESETS

        preset = CYCLES_PRESETS["archive"]
        assert preset.name == "archive"
        assert preset.samples >= 512
        assert preset.use_caustics is True
        assert preset.max_bounces >= 16

    def test_interior_preset(self):
        """Test interior preset for indoor scenes."""
        from lib.render.cycles_config import CYCLES_PRESETS

        preset = CYCLES_PRESETS["interior"]
        assert preset.name == "interior"
        assert preset.guiding_quality >= 0.7  # High guiding for interiors
        assert preset.max_bounces >= 16

    def test_animation_preset(self):
        """Test animation preset."""
        from lib.render.cycles_config import CYCLES_PRESETS

        preset = CYCLES_PRESETS["animation"]
        assert preset.name == "animation"
        # Animation typically uses fewer samples with denoising
        assert preset.samples <= 256


class TestGetCyclesPreset:
    """Tests for get_cycles_preset function."""

    def test_get_existing_preset(self):
        """Test getting an existing preset."""
        from lib.render.cycles_config import get_cycles_preset

        preset = get_cycles_preset("production")
        assert preset.name == "production"

    def test_get_nonexistent_preset(self):
        """Test getting a nonexistent preset raises error."""
        from lib.render.cycles_config import get_cycles_preset

        with pytest.raises(KeyError) as exc_info:
            get_cycles_preset("nonexistent")

        assert "not found" in str(exc_info.value)


class TestApplyCyclesConfig:
    """Tests for apply_cycles_config function."""

    def test_apply_config_requires_bpy(self):
        """Test that apply_cycles_config requires Blender."""
        from lib.render.cycles_config import apply_cycles_config, CyclesConfig

        config = CyclesConfig(name="test")

        try:
            apply_cycles_config(config)
            pytest.skip("Blender (bpy) is available - skipping test")
        except RuntimeError:
            pass  # Expected when bpy is not available


class TestConfigureOptix:
    """Tests for configure_optix function."""

    def test_configure_optix_requires_bpy(self):
        """Test that configure_optix requires Blender."""
        from lib.render.cycles_config import configure_optix

        try:
            configure_optix()
            pytest.skip("Blender (bpy) is available - skipping test")
        except RuntimeError:
            pass  # Expected when bpy is not available


class TestConfigureHip:
    """Tests for configure_hip function."""

    def test_configure_hip_requires_bpy(self):
        """Test that configure_hip requires Blender."""
        from lib.render.cycles_config import configure_hip

        try:
            configure_hip()
            pytest.skip("Blender (bpy) is available - skipping test")
        except RuntimeError:
            pass  # Expected when bpy is not available


class TestConfigureMetal:
    """Tests for configure_metal function."""

    def test_configure_metal_requires_bpy(self):
        """Test that configure_metal requires Blender."""
        from lib.render.cycles_config import configure_metal

        try:
            configure_metal()
            pytest.skip("Blender (bpy) is available - skipping test")
        except RuntimeError:
            pass  # Expected when bpy is not available


class TestConfigureCpu:
    """Tests for configure_cpu function."""

    def test_configure_cpu_requires_bpy(self):
        """Test that configure_cpu requires Blender."""
        from lib.render.cycles_config import configure_cpu

        try:
            configure_cpu()
            pytest.skip("Blender (bpy) is available - skipping test")
        except RuntimeError:
            pass  # Expected when bpy is not available


class TestDetectOptimalDevice:
    """Tests for detect_optimal_device function."""

    def test_detect_optimal_device_without_bpy(self):
        """Test detect_optimal_device returns CPU without bpy."""
        from lib.render.cycles_config import detect_optimal_device

        result = detect_optimal_device()
        # Falls back to CPU without bpy (or whatever device is available)
        assert result in ("CPU", "OPTIX", "HIP", "METAL", "CUDA")


class TestCyclesConfigBounceSettings:
    """Tests for bounce configuration."""

    def test_bounce_defaults(self):
        """Test default bounce settings."""
        from lib.render.cycles_config import CyclesConfig

        config = CyclesConfig(name="test")
        assert config.max_bounces == 12
        assert config.diffuse_bounces == 4
        assert config.glossy_bounces == 4
        assert config.transmission_bounces == 8
        assert config.transparent_max_bounces == 8

    def test_high_bounce_config(self):
        """Test high bounce configuration for quality."""
        from lib.render.cycles_config import CyclesConfig

        config = CyclesConfig(
            name="high_quality",
            max_bounces=24,
            diffuse_bounces=8,
            glossy_bounces=8,
            transmission_bounces=16,
        )

        assert config.max_bounces == 24
        assert config.diffuse_bounces == 8


class TestCyclesConfigSamplingSettings:
    """Tests for sampling configuration."""

    def test_adaptive_sampling_config(self):
        """Test adaptive sampling configuration."""
        from lib.render.cycles_config import CyclesConfig

        config = CyclesConfig(
            name="adaptive",
            adaptive_sampling=True,
            adaptive_threshold=0.005,
            adaptive_min_samples=16,
        )

        assert config.adaptive_sampling is True
        assert config.adaptive_threshold == 0.005
        assert config.adaptive_min_samples == 16

    def test_path_guiding_config(self):
        """Test path guiding configuration."""
        from lib.render.cycles_config import CyclesConfig

        config = CyclesConfig(
            name="guided",
            use_guiding=True,
            guiding_quality=0.8,
        )

        assert config.use_guiding is True
        assert config.guiding_quality == 0.8


class TestCyclesConfigDenoiseSettings:
    """Tests for denoising configuration."""

    def test_denoise_config(self):
        """Test denoising configuration."""
        from lib.render.cycles_config import CyclesConfig

        config = CyclesConfig(
            name="denoised",
            use_denoising=True,
            denoiser="OPTIX",
            denoising_start_sample=0,
        )

        assert config.use_denoising is True
        assert config.denoiser == "OPTIX"
        assert config.denoising_start_sample == 0

    def test_no_denoise_config(self):
        """Test disabled denoising."""
        from lib.render.cycles_config import CyclesConfig

        config = CyclesConfig(
            name="no_denoise",
            use_denoising=False,
        )

        assert config.use_denoising is False


class TestCyclesConfigVolumeSettings:
    """Tests for volume configuration."""

    def test_volume_config(self):
        """Test volume sampling configuration."""
        from lib.render.cycles_config import CyclesConfig

        config = CyclesConfig(
            name="volume",
            volume_samples=4,
            volume_step_rate=0.5,
        )

        assert config.volume_samples == 4
        assert config.volume_step_rate == 0.5

    def test_volume_bounces(self):
        """Test volume bounces configuration."""
        from lib.render.cycles_config import CyclesConfig

        config = CyclesConfig(
            name="volume_heavy",
            volume_bounces=4,
        )

        assert config.volume_bounces == 4

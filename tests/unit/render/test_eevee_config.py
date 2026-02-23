"""
Tests for render/eevee_config module.

Tests run WITHOUT Blender (bpy) by testing only non-Blender-dependent code paths.
"""

import pytest


class TestRaytracingMethod:
    """Tests for RaytracingMethod enum."""

    def test_raytracing_method_values(self):
        """Test RaytracingMethod enum values."""
        from lib.render.eevee_config import RaytracingMethod

        assert RaytracingMethod.PROBE.value == "PROBE"
        assert RaytracingMethod.RAYTRACED.value == "RAYTRACED"


class TestShadowMethod:
    """Tests for ShadowMethod enum."""

    def test_shadow_method_values(self):
        """Test ShadowMethod enum values."""
        from lib.render.eevee_config import ShadowMethod

        assert ShadowMethod.ESIM.value == "ESIM"
        assert ShadowMethod.SHADOW_MAP.value == "SHADOW_MAP"


class TestEEVEENextConfig:
    """Tests for EEVEENextConfig dataclass."""

    def test_config_creation(self):
        """Test creating an EEVEENextConfig."""
        from lib.render.eevee_config import EEVEENextConfig

        config = EEVEENextConfig(
            name="test_config",
            taa_samples=64,
            use_raytracing=True,
        )

        assert config.name == "test_config"
        assert config.taa_samples == 64
        assert config.use_raytracing is True

    def test_config_defaults(self):
        """Test EEVEENextConfig default values."""
        from lib.render.eevee_config import EEVEENextConfig

        config = EEVEENextConfig(name="default")
        assert config.taa_samples == 32
        assert config.taa_reprojection is True
        assert config.use_raytracing is True
        assert config.raytracing_method == "PROBE"
        assert config.use_gtao is True
        assert config.use_sss is True

    def test_config_to_dict(self):
        """Test EEVEENextConfig serialization."""
        from lib.render.eevee_config import EEVEENextConfig

        config = EEVEENextConfig(
            name="test",
            taa_samples=128,
            use_raytracing=True,
        )
        data = config.to_dict()

        assert data["name"] == "test"
        assert data["taa_samples"] == 128
        assert data["use_raytracing"] is True


class TestEEVEEPresets:
    """Tests for EEVEE_PRESETS constant."""

    def test_presets_dict(self):
        """Test that EEVEE_PRESETS is a dictionary."""
        from lib.render.eevee_config import EEVEE_PRESETS

        assert isinstance(EEVEE_PRESETS, dict)
        assert len(EEVEE_PRESETS) > 0

    def test_viewport_preset(self):
        """Test viewport preset."""
        from lib.render.eevee_config import EEVEE_PRESETS

        preset = EEVEE_PRESETS["viewport"]
        assert preset.name == "viewport"
        assert preset.taa_samples <= 16
        assert preset.use_raytracing is False  # Viewport is fast

    def test_preview_preset(self):
        """Test preview preset."""
        from lib.render.eevee_config import EEVEE_PRESETS

        preset = EEVEE_PRESETS["preview"]
        assert preset.name == "preview"
        assert preset.taa_samples >= 8
        assert preset.use_raytracing is True

    def test_production_preset(self):
        """Test production preset."""
        from lib.render.eevee_config import EEVEE_PRESETS

        preset = EEVEE_PRESETS["production"]
        assert preset.name == "production"
        assert preset.taa_samples >= 32
        assert preset.use_raytracing is True
        assert preset.raytracing_samples >= 3

    def test_high_quality_preset(self):
        """Test high quality preset."""
        from lib.render.eevee_config import EEVEE_PRESETS

        preset = EEVEE_PRESETS["high_quality"]
        assert preset.name == "high_quality"
        assert preset.taa_samples >= 64
        assert preset.raytracing_method == "RAYTRACED"
        assert preset.gtao_quality >= 0.9

    def test_animation_preset(self):
        """Test animation preset."""
        from lib.render.eevee_config import EEVEE_PRESETS

        preset = EEVEE_PRESETS["animation"]
        assert preset.name == "animation"
        # Animation typically disables reprojection for stability
        assert preset.taa_reprojection is False

    def test_product_preset(self):
        """Test product visualization preset."""
        from lib.render.eevee_config import EEVEE_PRESETS

        preset = EEVEE_PRESETS["product"]
        assert preset.name == "product"
        assert preset.raytracing_method == "RAYTRACED"
        assert preset.raytracing_resolution == 1.0

    def test_interior_preset(self):
        """Test interior preset."""
        from lib.render.eevee_config import EEVEE_PRESETS

        preset = EEVEE_PRESETS["interior"]
        assert preset.name == "interior"
        assert preset.use_volumetric is True
        assert preset.gtao_quality >= 0.9
        assert preset.use_fast_gi is True


class TestGetEEVEEPreset:
    """Tests for get_eevee_preset function."""

    def test_get_existing_preset(self):
        """Test getting an existing preset."""
        from lib.render.eevee_config import get_eevee_preset

        preset = get_eevee_preset("production")
        assert preset.name == "production"

    def test_get_nonexistent_preset(self):
        """Test getting a nonexistent preset raises error."""
        from lib.render.eevee_config import get_eevee_preset

        with pytest.raises(KeyError) as exc_info:
            get_eevee_preset("nonexistent")

        assert "not found" in str(exc_info.value)


class TestApplyEEVEEConfig:
    """Tests for apply_eevee_config function."""

    def test_apply_config_requires_bpy(self):
        """Test that apply_eevee_config requires Blender."""
        from lib.render.eevee_config import apply_eevee_config, EEVEENextConfig

        config = EEVEENextConfig(name="test")

        try:
            apply_eevee_config(config)
            pytest.skip("Blender (bpy) is available - skipping test")
        except RuntimeError:
            pass  # Expected when bpy is not available


class TestConfigureRaytracing:
    """Tests for configure_raytracing function."""

    def test_configure_raytracing_requires_bpy(self):
        """Test that configure_raytracing requires Blender."""
        from lib.render.eevee_config import configure_raytracing

        try:
            configure_raytracing()
            pytest.skip("Blender (bpy) is available - skipping test")
        except RuntimeError:
            pass  # Expected when bpy is not available


class TestConfigureTAA:
    """Tests for configure_taa function."""

    def test_configure_taa_requires_bpy(self):
        """Test that configure_taa requires Blender."""
        from lib.render.eevee_config import configure_taa

        try:
            configure_taa()
            pytest.skip("Blender (bpy) is available - skipping test")
        except RuntimeError:
            pass  # Expected when bpy is not available


class TestConfigureVolumetrics:
    """Tests for configure_volumetrics function."""

    def test_configure_volumetrics_requires_bpy(self):
        """Test that configure_volumetrics requires Blender."""
        from lib.render.eevee_config import configure_volumetrics

        try:
            configure_volumetrics()
            pytest.skip("Blender (bpy) is available - skipping test")
        except RuntimeError:
            pass  # Expected when bpy is not available


class TestEEVEEConfigTAASettings:
    """Tests for TAA configuration."""

    def test_taa_samples_range(self):
        """Test TAA samples within valid range."""
        from lib.render.eevee_config import EEVEENextConfig

        # Low samples
        config1 = EEVEENextConfig(name="low", taa_samples=8)
        assert config1.taa_samples == 8

        # High samples
        config2 = EEVEENextConfig(name="high", taa_samples=128)
        assert config2.taa_samples == 128

    def test_taa_reprojection_toggle(self):
        """Test TAA reprojection toggle."""
        from lib.render.eevee_config import EEVEENextConfig

        config1 = EEVEENextConfig(name="on", taa_reprojection=True)
        assert config1.taa_reprojection is True

        config2 = EEVEENextConfig(name="off", taa_reprojection=False)
        assert config2.taa_reprojection is False


class TestEEVEEConfigRaytracingSettings:
    """Tests for raytracing configuration."""

    def test_raytracing_method(self):
        """Test raytracing method selection."""
        from lib.render.eevee_config import EEVEENextConfig

        config1 = EEVEENextConfig(name="probe", raytracing_method="PROBE")
        assert config1.raytracing_method == "PROBE"

        config2 = EEVEENextConfig(name="traced", raytracing_method="RAYTRACED")
        assert config2.raytracing_method == "RAYTRACED"

    def test_raytracing_samples(self):
        """Test raytracing samples configuration."""
        from lib.render.eevee_config import EEVEENextConfig

        config = EEVEENextConfig(
            name="test",
            raytracing_samples=6,
            raytracing_resolution=1.0,
        )

        assert config.raytracing_samples == 6
        assert config.raytracing_resolution == 1.0

    def test_raytracing_resolution_scale(self):
        """Test raytracing resolution scale."""
        from lib.render.eevee_config import EEVEENextConfig

        config = EEVEENextConfig(
            name="test",
            raytracing_resolution=0.5,
        )

        assert config.raytracing_resolution == 0.5


class TestEEVEEConfigGTAOSettings:
    """Tests for GTAO configuration."""

    def test_gtao_quality(self):
        """Test GTAO quality settings."""
        from lib.render.eevee_config import EEVEENextConfig

        config = EEVEENextConfig(
            name="test",
            use_gtao=True,
            gtao_quality=0.75,
        )

        assert config.use_gtao is True
        assert config.gtao_quality == 0.75

    def test_gtao_disabled(self):
        """Test GTAO disabled."""
        from lib.render.eevee_config import EEVEENextConfig

        config = EEVEENextConfig(name="test", use_gtao=False)
        assert config.use_gtao is False


class TestEEVEEConfigSSSSettings:
    """Tests for SSS configuration."""

    def test_sss_config(self):
        """Test SSS configuration."""
        from lib.render.eevee_config import EEVEENextConfig

        config = EEVEENextConfig(
            name="test",
            use_sss=True,
            sss_samples=32,
            sss_jitter_threshold=0.25,
        )

        assert config.use_sss is True
        assert config.sss_samples == 32
        assert config.sss_jitter_threshold == 0.25


class TestEEVEEConfigVolumetricSettings:
    """Tests for volumetric configuration."""

    def test_volumetric_config(self):
        """Test volumetric configuration."""
        from lib.render.eevee_config import EEVEENextConfig

        config = EEVEENextConfig(
            name="test",
            use_volumetric=True,
            volumetric_samples=128,
            volumetric_tile_size=2,
        )

        assert config.use_volumetric is True
        assert config.volumetric_samples == 128
        assert config.volumetric_tile_size == 2

    def test_volumetric_disabled(self):
        """Test volumetric disabled."""
        from lib.render.eevee_config import EEVEENextConfig

        config = EEVEENextConfig(name="test", use_volumetric=False)
        assert config.use_volumetric is False


class TestEEVEEConfigShadowSettings:
    """Tests for shadow configuration."""

    def test_shadow_config(self):
        """Test shadow configuration."""
        from lib.render.eevee_config import EEVEENextConfig

        config = EEVEENextConfig(
            name="test",
            shadow_method="ESIM",
            shadow_resolution=4096,
            use_soft_shadows=True,
        )

        assert config.shadow_method == "ESIM"
        assert config.shadow_resolution == 4096
        assert config.use_soft_shadows is True


class TestEEVEEConfigGISettings:
    """Tests for GI configuration."""

    def test_gi_config(self):
        """Test GI configuration."""
        from lib.render.eevee_config import EEVEENextConfig

        config = EEVEENextConfig(
            name="test",
            gi_distance=200.0,
            gi_cubemap_resolution=1024,
            gi_visibility_samples=64,
            use_fast_gi=True,
        )

        assert config.gi_distance == 200.0
        assert config.gi_cubemap_resolution == 1024
        assert config.gi_visibility_samples == 64
        assert config.use_fast_gi is True


class TestEEVEEConfigOverscan:
    """Tests for overscan configuration."""

    def test_overscan_config(self):
        """Test overscan configuration."""
        from lib.render.eevee_config import EEVEENextConfig

        config = EEVEENextConfig(name="test", overscan=5.0)
        assert config.overscan == 5.0

    def test_no_overscan(self):
        """Test no overscan."""
        from lib.render.eevee_config import EEVEENextConfig

        config = EEVEENextConfig(name="test", overscan=0.0)
        assert config.overscan == 0.0

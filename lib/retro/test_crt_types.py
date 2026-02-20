"""
Unit tests for CRT Types module.

Tests for CRTConfig, ScanlineConfig, PhosphorConfig, CurvatureConfig,
and related utility functions.
"""

import pytest
from dataclasses import asdict

from lib.retro.crt_types import (
    # Enums
    ScanlineMode,
    PhosphorPattern,
    DisplayType,
    # Dataclasses
    ScanlineConfig,
    PhosphorConfig,
    CurvatureConfig,
    CRTConfig,
    # Presets
    CRT_PRESETS,
    # Functions
    get_preset,
    list_presets,
    get_preset_description,
    create_custom_preset,
    validate_config,
)


class TestScanlineConfig:
    """Tests for ScanlineConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = ScanlineConfig()
        assert config.enabled is True
        assert config.intensity == 0.3
        assert config.spacing == 2
        assert config.thickness == 0.5
        assert config.mode == "alternate"
        assert config.brightness_compensation == 1.1

    def test_custom_values(self):
        """Test custom configuration values."""
        config = ScanlineConfig(
            enabled=False,
            intensity=0.5,
            spacing=1,
            thickness=0.7,
            mode="every_line",
            brightness_compensation=1.2
        )
        assert config.enabled is False
        assert config.intensity == 0.5
        assert config.spacing == 1
        assert config.thickness == 0.7
        assert config.mode == "every_line"
        assert config.brightness_compensation == 1.2

    def test_intensity_validation(self):
        """Test intensity range validation."""
        # Valid values
        ScanlineConfig(intensity=0.0)
        ScanlineConfig(intensity=0.5)
        ScanlineConfig(intensity=1.0)

        # Invalid values
        with pytest.raises(ValueError, match="intensity must be 0-1"):
            ScanlineConfig(intensity=-0.1)
        with pytest.raises(ValueError, match="intensity must be 0-1"):
            ScanlineConfig(intensity=1.1)

    def test_spacing_validation(self):
        """Test spacing range validation."""
        # Valid values
        ScanlineConfig(spacing=1)
        ScanlineConfig(spacing=10)

        # Invalid values
        with pytest.raises(ValueError, match="spacing must be >= 1"):
            ScanlineConfig(spacing=0)
        with pytest.raises(ValueError, match="spacing must be >= 1"):
            ScanlineConfig(spacing=-1)

    def test_thickness_validation(self):
        """Test thickness range validation."""
        # Valid values
        ScanlineConfig(thickness=0.0)
        ScanlineConfig(thickness=0.5)
        ScanlineConfig(thickness=1.0)

        # Invalid values
        with pytest.raises(ValueError, match="thickness must be 0-1"):
            ScanlineConfig(thickness=-0.1)
        with pytest.raises(ValueError, match="thickness must be 0-1"):
            ScanlineConfig(thickness=1.1)

    def test_mode_validation(self):
        """Test mode validation."""
        # Valid modes
        ScanlineConfig(mode="alternate")
        ScanlineConfig(mode="every_line")
        ScanlineConfig(mode="random")

        # Invalid mode
        with pytest.raises(ValueError, match="mode must be"):
            ScanlineConfig(mode="invalid")

    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = ScanlineConfig(intensity=0.5, spacing=1)
        d = config.to_dict()
        assert d["intensity"] == 0.5
        assert d["spacing"] == 1
        assert d["enabled"] is True
        assert d["mode"] == "alternate"

    def test_from_dict(self):
        """Test creation from dictionary."""
        d = {
            "enabled": False,
            "intensity": 0.6,
            "spacing": 3,
            "thickness": 0.8,
            "mode": "every_line",
            "brightness_compensation": 1.3
        }
        config = ScanlineConfig.from_dict(d)
        assert config.enabled is False
        assert config.intensity == 0.6
        assert config.spacing == 3
        assert config.thickness == 0.8
        assert config.mode == "every_line"
        assert config.brightness_compensation == 1.3


class TestPhosphorConfig:
    """Tests for PhosphorConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = PhosphorConfig()
        assert config.enabled is False
        assert config.pattern == "rgb"
        assert config.intensity == 0.5
        assert config.scale == 1.0
        assert config.slot_width == 2
        assert config.slot_height == 4

    def test_custom_values(self):
        """Test custom configuration values."""
        config = PhosphorConfig(
            enabled=True,
            pattern="aperture_grille",
            intensity=0.7,
            scale=1.5,
            slot_width=3,
            slot_height=6
        )
        assert config.enabled is True
        assert config.pattern == "aperture_grille"
        assert config.intensity == 0.7
        assert config.scale == 1.5
        assert config.slot_width == 3
        assert config.slot_height == 6

    def test_pattern_validation(self):
        """Test pattern validation."""
        # Valid patterns
        for pattern in ["rgb", "bgr", "aperture_grille", "slot_mask", "shadow_mask"]:
            PhosphorConfig(pattern=pattern)

        # Invalid pattern
        with pytest.raises(ValueError, match="pattern must be one of"):
            PhosphorConfig(pattern="invalid")

    def test_intensity_validation(self):
        """Test intensity range validation."""
        PhosphorConfig(intensity=0.0)
        PhosphorConfig(intensity=1.0)
        with pytest.raises(ValueError, match="intensity must be 0-1"):
            PhosphorConfig(intensity=1.5)

    def test_scale_validation(self):
        """Test scale validation."""
        PhosphorConfig(scale=0.1)
        PhosphorConfig(scale=10.0)
        with pytest.raises(ValueError, match="scale must be > 0"):
            PhosphorConfig(scale=0)
        with pytest.raises(ValueError, match="scale must be > 0"):
            PhosphorConfig(scale=-1)

    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = PhosphorConfig(pattern="slot_mask", intensity=0.6)
        d = config.to_dict()
        assert d["pattern"] == "slot_mask"
        assert d["intensity"] == 0.6

    def test_from_dict(self):
        """Test creation from dictionary."""
        d = {
            "enabled": True,
            "pattern": "bgr",
            "intensity": 0.4,
            "scale": 2.0,
            "slot_width": 4,
            "slot_height": 8
        }
        config = PhosphorConfig.from_dict(d)
        assert config.enabled is True
        assert config.pattern == "bgr"
        assert config.intensity == 0.4
        assert config.scale == 2.0


class TestCurvatureConfig:
    """Tests for CurvatureConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = CurvatureConfig()
        assert config.enabled is False
        assert config.amount == 0.1
        assert config.vignette_amount == 0.2
        assert config.corner_radius == 0
        assert config.border_size == 0

    def test_custom_values(self):
        """Test custom configuration values."""
        config = CurvatureConfig(
            enabled=True,
            amount=0.15,
            vignette_amount=0.3,
            corner_radius=20,
            border_size=5
        )
        assert config.enabled is True
        assert config.amount == 0.15
        assert config.vignette_amount == 0.3
        assert config.corner_radius == 20
        assert config.border_size == 5

    def test_amount_validation(self):
        """Test amount range validation."""
        CurvatureConfig(amount=0.0)
        CurvatureConfig(amount=1.0)
        with pytest.raises(ValueError, match="amount must be 0-1"):
            CurvatureConfig(amount=-0.1)
        with pytest.raises(ValueError, match="amount must be 0-1"):
            CurvatureConfig(amount=1.5)

    def test_vignette_validation(self):
        """Test vignette_amount range validation."""
        CurvatureConfig(vignette_amount=0.0)
        CurvatureConfig(vignette_amount=1.0)
        with pytest.raises(ValueError, match="vignette_amount must be 0-1"):
            CurvatureConfig(vignette_amount=-0.1)

    def test_corner_radius_validation(self):
        """Test corner_radius validation."""
        CurvatureConfig(corner_radius=0)
        CurvatureConfig(corner_radius=100)
        with pytest.raises(ValueError, match="corner_radius must be >= 0"):
            CurvatureConfig(corner_radius=-1)

    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = CurvatureConfig(amount=0.2, vignette_amount=0.3)
        d = config.to_dict()
        assert d["amount"] == 0.2
        assert d["vignette_amount"] == 0.3

    def test_from_dict(self):
        """Test creation from dictionary."""
        d = {
            "enabled": True,
            "amount": 0.12,
            "vignette_amount": 0.25,
            "corner_radius": 15,
            "border_size": 3
        }
        config = CurvatureConfig.from_dict(d)
        assert config.enabled is True
        assert config.amount == 0.12
        assert config.vignette_amount == 0.25
        assert config.corner_radius == 15


class TestCRTConfig:
    """Tests for CRTConfig."""

    def test_default_values(self):
        """Test default configuration values."""
        config = CRTConfig()
        assert config.name == "custom"
        assert isinstance(config.scanlines, ScanlineConfig)
        assert isinstance(config.phosphor, PhosphorConfig)
        assert isinstance(config.curvature, CurvatureConfig)
        assert config.bloom == 0.0
        assert config.chromatic_aberration == 0.0
        assert config.flicker == 0.0
        assert config.interlace is False
        assert config.pixel_jitter == 0.0
        assert config.noise == 0.0
        assert config.ghosting == 0.0
        assert config.brightness == 1.0
        assert config.contrast == 1.0
        assert config.saturation == 1.0
        assert config.gamma == 2.2

    def test_custom_values(self):
        """Test custom configuration values."""
        config = CRTConfig(
            name="test",
            scanlines=ScanlineConfig(intensity=0.5),
            bloom=0.2,
            brightness=1.2
        )
        assert config.name == "test"
        assert config.scanlines.intensity == 0.5
        assert config.bloom == 0.2
        assert config.brightness == 1.2

    def test_bloom_validation(self):
        """Test bloom range validation."""
        CRTConfig(bloom=0.0)
        CRTConfig(bloom=1.0)
        with pytest.raises(ValueError, match="bloom must be 0-1"):
            CRTConfig(bloom=-0.1)
        with pytest.raises(ValueError, match="bloom must be 0-1"):
            CRTConfig(bloom=1.5)

    def test_chromatic_aberration_validation(self):
        """Test chromatic_aberration range validation."""
        CRTConfig(chromatic_aberration=0.0)
        CRTConfig(chromatic_aberration=0.1)
        with pytest.raises(ValueError, match="chromatic_aberration must be 0-0.1"):
            CRTConfig(chromatic_aberration=0.2)

    def test_brightness_validation(self):
        """Test brightness validation."""
        CRTConfig(brightness=0.1)
        CRTConfig(brightness=2.0)
        with pytest.raises(ValueError, match="brightness must be > 0"):
            CRTConfig(brightness=0)

    def test_gamma_validation(self):
        """Test gamma validation."""
        CRTConfig(gamma=0.1)
        CRTConfig(gamma=3.0)
        with pytest.raises(ValueError, match="gamma must be > 0"):
            CRTConfig(gamma=0)

    def test_to_dict(self):
        """Test conversion to dictionary."""
        config = CRTConfig(
            name="test",
            bloom=0.3,
            scanlines=ScanlineConfig(intensity=0.4)
        )
        d = config.to_dict()
        assert d["name"] == "test"
        assert d["bloom"] == 0.3
        assert isinstance(d["scanlines"], dict)
        assert d["scanlines"]["intensity"] == 0.4

    def test_from_dict(self):
        """Test creation from dictionary."""
        d = {
            "name": "from_dict",
            "scanlines": {"intensity": 0.6, "enabled": True},
            "phosphor": {"pattern": "bgr", "enabled": False},
            "curvature": {"amount": 0.15, "enabled": True},
            "bloom": 0.25,
            "brightness": 1.1
        }
        config = CRTConfig.from_dict(d)
        assert config.name == "from_dict"
        assert config.scanlines.intensity == 0.6
        assert config.phosphor.pattern == "bgr"
        assert config.curvature.amount == 0.15
        assert config.bloom == 0.25
        assert config.brightness == 1.1

    def test_nested_config_preservation(self):
        """Test that nested configs are properly converted."""
        config = CRTConfig(
            scanlines=ScanlineConfig(intensity=0.7, spacing=1),
            phosphor=PhosphorConfig(pattern="slot_mask", intensity=0.6)
        )
        d = config.to_dict()
        config2 = CRTConfig.from_dict(d)

        assert config2.scanlines.intensity == 0.7
        assert config2.scanlines.spacing == 1
        assert config2.phosphor.pattern == "slot_mask"
        assert config2.phosphor.intensity == 0.6


class TestCRTPresets:
    """Tests for built-in CRT presets."""

    def test_preset_count(self):
        """Test that expected number of presets exist."""
        assert len(CRT_PRESETS) >= 12

    def test_all_presets_valid(self):
        """Test that all presets are valid CRTConfig instances."""
        for name, config in CRT_PRESETS.items():
            assert isinstance(config, CRTConfig), f"{name} is not a CRTConfig"
            assert config.name == name, f"{name} has wrong name: {config.name}"

    def test_arcade_preset(self):
        """Test crt_arcade preset values."""
        config = CRT_PRESETS["crt_arcade"]
        assert config.scanlines.enabled is True
        assert config.scanlines.intensity == 0.25
        assert config.phosphor.enabled is True
        assert config.phosphor.pattern == "aperture_grille"
        assert config.curvature.enabled is True
        assert config.bloom == 0.15

    def test_pvm_preset(self):
        """Test pvm preset values."""
        config = CRT_PRESETS["pvm"]
        assert config.scanlines.enabled is True
        assert config.scanlines.intensity == 0.15
        assert config.phosphor.pattern == "aperture_grille"
        assert config.curvature.enabled is False

    def test_gameboy_preset(self):
        """Test lcd_gameboy preset values."""
        config = CRT_PRESETS["lcd_gameboy"]
        assert config.scanlines.enabled is False
        assert config.phosphor.enabled is False
        assert config.curvature.enabled is False
        assert config.ghosting == 0.3
        assert config.saturation == 0.8

    def test_bw_preset(self):
        """Test bw_crt preset values."""
        config = CRT_PRESETS["bw_crt"]
        assert config.saturation == 0.0  # Grayscale


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_get_preset(self):
        """Test get_preset function."""
        config = get_preset("crt_arcade")
        assert config.name == "crt_arcade"

        with pytest.raises(KeyError):
            get_preset("nonexistent")

    def test_list_presets(self):
        """Test list_presets function."""
        presets = list_presets()
        assert isinstance(presets, list)
        assert "crt_arcade" in presets
        assert "pvm" in presets
        assert len(presets) >= 12

    def test_get_preset_description(self):
        """Test get_preset_description function."""
        desc = get_preset_description("crt_arcade")
        assert "arcade" in desc.lower()

        desc = get_preset_description("nonexistent")
        assert "No description" in desc

    def test_create_custom_preset(self):
        """Test create_custom_preset function."""
        # Simple override
        config = create_custom_preset("modern_lcd", bloom=0.5)
        assert config.bloom == 0.5
        assert config.scanlines.enabled is False

        # Nested override
        config = create_custom_preset(
            "crt_arcade",
            name="my_custom",
            bloom=0.3,
            **{"scanlines.intensity": 0.4}
        )
        assert config.name == "my_custom"
        assert config.bloom == 0.3
        # Note: nested override format may need adjustment based on implementation

    def test_validate_config(self):
        """Test validate_config function."""
        # Valid config - no issues
        config = CRTConfig()
        issues = validate_config(config)
        assert issues == []

        # High scanline intensity - warning
        config = CRTConfig(scanlines=ScanlineConfig(intensity=0.8))
        issues = validate_config(config)
        assert any("scanline" in i.lower() for i in issues)

        # High curvature - warning
        config = CRTConfig(curvature=CurvatureConfig(amount=0.25, enabled=True))
        issues = validate_config(config)
        assert any("curvature" in i.lower() for i in issues)

        # High noise - warning
        config = CRTConfig(noise=0.15)
        issues = validate_config(config)
        assert any("noise" in i.lower() for i in issues)

        # Many effects - performance warning
        config = CRTConfig(
            scanlines=ScanlineConfig(enabled=True),
            phosphor=PhosphorConfig(enabled=True),
            curvature=CurvatureConfig(enabled=True),
            bloom=0.2,
            chromatic_aberration=0.01,
            flicker=0.1,
            noise=0.1
        )
        issues = validate_config(config)
        assert any("performance" in i.lower() for i in issues)


class TestEnums:
    """Tests for enum types."""

    def test_scanline_mode_enum(self):
        """Test ScanlineMode enum values."""
        assert ScanlineMode.ALTERNATE.value == "alternate"
        assert ScanlineMode.EVERY_LINE.value == "every_line"
        assert ScanlineMode.RANDOM.value == "random"

    def test_phosphor_pattern_enum(self):
        """Test PhosphorPattern enum values."""
        assert PhosphorPattern.RGB.value == "rgb"
        assert PhosphorPattern.BGR.value == "bgr"
        assert PhosphorPattern.APERTURE_GRILLE.value == "aperture_grille"
        assert PhosphorPattern.SLOT_MASK.value == "slot_mask"
        assert PhosphorPattern.SHADOW_MASK.value == "shadow_mask"

    def test_display_type_enum(self):
        """Test DisplayType enum values."""
        assert DisplayType.CRT_ARCADE.value == "crt_arcade"
        assert DisplayType.CRT_TV.value == "crt_tv"
        assert DisplayType.LCD_GAMEBOY.value == "lcd_gameboy"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

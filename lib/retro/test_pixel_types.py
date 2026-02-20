"""
Tests for pixel_types module.

Run with: pytest lib/retro/test_pixel_types.py -v
"""

import pytest
from lib.retro.pixel_types import (
    PixelMode,
    AspectRatioMode,
    ScalingFilter,
    DitherMode,
    SubPixelLayout,
    PixelStyle,
    PixelationConfig,
    PixelationResult,
    ColorPalette,
    BUILTIN_PALETTES,
    get_palette,
    list_palettes,
    GAMEBOY_PALETTE,
    NES_PALETTE,
    PICO8_PALETTE,
    CGA_PALETTE,
    MACPLUS_PALETTE,
    EGA_PALETTE,
)


class TestPixelStyle:
    """Tests for PixelStyle dataclass."""

    def test_default_values(self):
        """Test default configuration."""
        style = PixelStyle()
        assert style.mode == "16bit"
        assert style.pixel_size == 1
        assert style.color_limit == 256
        assert style.preserve_edges is True
        assert style.posterize_levels == 0
        assert style.sub_pixel_layout == "none"
        assert style.dither_mode == "none"
        assert style.dither_strength == 1.0

    def test_to_dict(self):
        """Test serialization to dictionary."""
        style = PixelStyle(mode="8bit", pixel_size=2, color_limit=16)
        d = style.to_dict()
        assert d["mode"] == "8bit"
        assert d["pixel_size"] == 2
        assert d["color_limit"] == 16

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        d = {"mode": "4bit", "pixel_size": 3, "color_limit": 4}
        style = PixelStyle.from_dict(d)
        assert style.mode == "4bit"
        assert style.pixel_size == 3
        assert style.color_limit == 4

    def test_roundtrip(self):
        """Test to_dict/from_dict roundtrip."""
        original = PixelStyle(mode="1bit", pixel_size=4, dither_mode="floyd_steinberg")
        restored = PixelStyle.from_dict(original.to_dict())
        assert restored.mode == original.mode
        assert restored.pixel_size == original.pixel_size
        assert restored.dither_mode == original.dither_mode

    def test_validate_valid(self):
        """Test validation with valid config."""
        style = PixelStyle()
        errors = style.validate()
        assert len(errors) == 0

    def test_validate_invalid_mode(self):
        """Test validation catches invalid mode."""
        style = PixelStyle(mode="invalid")
        errors = style.validate()
        assert len(errors) == 1
        assert "mode" in errors[0]

    def test_validate_invalid_pixel_size(self):
        """Test validation catches invalid pixel_size."""
        style = PixelStyle(pixel_size=0)
        errors = style.validate()
        assert len(errors) == 1
        assert "pixel_size" in errors[0]

    def test_validate_invalid_color_limit(self):
        """Test validation catches invalid color_limit."""
        style = PixelStyle(color_limit=1)
        errors = style.validate()
        assert len(errors) == 1
        assert "color_limit" in errors[0]

    def test_validate_invalid_dither_strength(self):
        """Test validation catches invalid dither_strength."""
        style = PixelStyle(dither_strength=2.0)
        errors = style.validate()
        assert len(errors) == 1
        assert "dither_strength" in errors[0]

    def test_validate_invalid_dither_mode(self):
        """Test validation catches invalid dither_mode."""
        style = PixelStyle(dither_mode="invalid")
        errors = style.validate()
        assert len(errors) == 1
        assert "dither_mode" in errors[0]

    def test_validate_multiple_errors(self):
        """Test validation catches multiple errors."""
        style = PixelStyle(mode="bad", pixel_size=-1, color_limit=0)
        errors = style.validate()
        assert len(errors) >= 3


class TestPixelationConfig:
    """Tests for PixelationConfig dataclass."""

    def test_default_values(self):
        """Test default configuration."""
        config = PixelationConfig()
        assert config.target_resolution == (0, 0)
        assert config.aspect_ratio_mode == "preserve"
        assert config.scaling_filter == "nearest"
        assert config.edge_detection is True
        assert config.edge_threshold == 0.1
        assert config.output_scale == 1

    def test_to_dict(self):
        """Test serialization."""
        config = PixelationConfig(target_resolution=(320, 240))
        d = config.to_dict()
        assert d["target_resolution"] == [320, 240]

    def test_from_dict(self):
        """Test deserialization."""
        d = {"target_resolution": [160, 144], "scaling_filter": "bilinear"}
        config = PixelationConfig.from_dict(d)
        assert config.target_resolution == (160, 144)
        assert config.scaling_filter == "bilinear"

    def test_with_style(self):
        """Test config with nested style."""
        config = PixelationConfig(style=PixelStyle(mode="8bit"))
        d = config.to_dict()
        assert d["style"]["mode"] == "8bit"

        restored = PixelationConfig.from_dict(d)
        assert restored.style.mode == "8bit"

    def test_validate_valid(self):
        """Test validation with valid config."""
        config = PixelationConfig()
        errors = config.validate()
        assert len(errors) == 0

    def test_validate_invalid_aspect_ratio(self):
        """Test validation catches invalid aspect ratio mode."""
        config = PixelationConfig(aspect_ratio_mode="invalid")
        errors = config.validate()
        assert any("aspect_ratio_mode" in e for e in errors)

    def test_validate_invalid_scaling_filter(self):
        """Test validation catches invalid scaling filter."""
        config = PixelationConfig(scaling_filter="invalid")
        errors = config.validate()
        assert any("scaling_filter" in e for e in errors)

    def test_validate_invalid_edge_threshold(self):
        """Test validation catches invalid edge threshold."""
        config = PixelationConfig(edge_threshold=2.0)
        errors = config.validate()
        assert any("edge_threshold" in e for e in errors)

    def test_validate_invalid_output_scale(self):
        """Test validation catches invalid output scale."""
        config = PixelationConfig(output_scale=0)
        errors = config.validate()
        assert any("output_scale" in e for e in errors)

    def test_for_console_snes(self):
        """Test SNES preset."""
        config = PixelationConfig.for_console("snes")
        assert config.target_resolution == (256, 224)
        assert config.style.mode == "16bit"
        assert config.style.color_limit == 256

    def test_for_console_nes(self):
        """Test NES preset."""
        config = PixelationConfig.for_console("nes")
        assert config.target_resolution == (256, 240)
        assert config.style.mode == "8bit"
        assert config.style.color_limit == 54

    def test_for_console_gameboy(self):
        """Test Game Boy preset."""
        config = PixelationConfig.for_console("gameboy")
        assert config.target_resolution == (160, 144)
        assert config.style.mode == "4bit"
        assert config.style.color_limit == 4

    def test_for_console_pico8(self):
        """Test PICO-8 preset."""
        config = PixelationConfig.for_console("pico8")
        assert config.target_resolution == (128, 128)
        assert config.style.mode == "8bit"
        assert config.style.color_limit == 16

    def test_for_console_mac_plus(self):
        """Test Mac Plus preset."""
        config = PixelationConfig.for_console("mac_plus")
        assert config.target_resolution == (512, 342)
        assert config.style.mode == "1bit"
        assert config.style.color_limit == 2

    def test_for_console_unknown(self):
        """Test unknown console returns default."""
        config = PixelationConfig.for_console("unknown")
        assert config.target_resolution == (0, 0)
        assert config.style.mode == "16bit"


class TestPixelationResult:
    """Tests for PixelationResult dataclass."""

    def test_default_values(self):
        """Test default configuration."""
        result = PixelationResult()
        assert result.image is None
        assert result.original_resolution == (0, 0)
        assert result.color_count == 0
        assert result.processing_time == 0.0

    def test_to_dict(self):
        """Test serialization."""
        result = PixelationResult(
            original_resolution=(1920, 1080),
            pixel_resolution=(320, 180),
            output_resolution=(640, 360),
            color_count=16,
            processing_time=1.5,
        )
        d = result.to_dict()
        assert d["original_resolution"] == [1920, 1080]
        assert d["pixel_resolution"] == [320, 180]
        assert d["output_resolution"] == [640, 360]
        assert d["color_count"] == 16
        assert d["processing_time"] == 1.5


class TestColorPalette:
    """Tests for ColorPalette dataclass."""

    def test_default_values(self):
        """Test default configuration."""
        palette = ColorPalette()
        assert palette.name == ""
        assert len(palette.colors) == 0

    def test_to_dict(self):
        """Test serialization."""
        palette = ColorPalette(name="test", colors=[(255, 0, 0), (0, 255, 0)])
        d = palette.to_dict()
        assert d["name"] == "test"
        assert d["colors"] == [[255, 0, 0], [0, 255, 0]]

    def test_from_dict(self):
        """Test deserialization."""
        d = {"name": "test", "colors": [[255, 0, 0], [0, 255, 0]]}
        palette = ColorPalette.from_dict(d)
        assert palette.name == "test"
        assert palette.colors == [(255, 0, 0), (0, 255, 0)]

    def test_nearest_color_exact(self):
        """Test nearest color with exact match."""
        palette = ColorPalette(colors=[(255, 0, 0), (0, 255, 0), (0, 0, 255)])
        nearest = palette.nearest_color((255, 0, 0))
        assert nearest == (255, 0, 0)

    def test_nearest_color_close(self):
        """Test nearest color with close match."""
        palette = ColorPalette(colors=[(0, 0, 0), (255, 255, 255)])
        nearest = palette.nearest_color((10, 10, 10))
        assert nearest == (0, 0, 0)

    def test_nearest_color_empty_palette(self):
        """Test nearest color with empty palette returns input."""
        palette = ColorPalette()
        nearest = palette.nearest_color((128, 128, 128))
        assert nearest == (128, 128, 128)


class TestBuiltInPalettes:
    """Tests for built-in palettes."""

    def test_gameboy_palette(self):
        """Test Game Boy palette."""
        assert len(GAMEBOY_PALETTE.colors) == 4
        assert GAMEBOY_PALETTE.name == "gameboy"

    def test_nes_palette(self):
        """Test NES palette."""
        assert len(NES_PALETTE.colors) > 0
        assert NES_PALETTE.name == "nes"

    def test_pico8_palette(self):
        """Test PICO-8 palette has exactly 16 colors."""
        assert len(PICO8_PALETTE.colors) == 16
        assert PICO8_PALETTE.name == "pico8"

    def test_cga_palette(self):
        """Test CGA palette has exactly 4 colors."""
        assert len(CGA_PALETTE.colors) == 4
        assert CGA_PALETTE.name == "cga"

    def test_macplus_palette(self):
        """Test Mac Plus palette has exactly 2 colors."""
        assert len(MACPLUS_PALETTE.colors) == 2
        assert MACPLUS_PALETTE.name == "mac_plus"

    def test_ega_palette(self):
        """Test EGA palette has exactly 16 colors."""
        assert len(EGA_PALETTE.colors) == 16
        assert EGA_PALETTE.name == "ega"

    def test_builtin_palettes_dict(self):
        """Test built-in palettes dictionary."""
        assert "gameboy" in BUILTIN_PALETTES
        assert "nes" in BUILTIN_PALETTES
        assert "pico8" in BUILTIN_PALETTES
        assert "cga" in BUILTIN_PALETTES
        assert "mac_plus" in BUILTIN_PALETTES
        assert "ega" in BUILTIN_PALETTES

    def test_get_palette(self):
        """Test get_palette function."""
        palette = get_palette("pico8")
        assert palette is not None
        assert palette.name == "pico8"

    def test_get_palette_case_insensitive(self):
        """Test get_palette is case-insensitive."""
        palette = get_palette("PICO8")
        assert palette is not None
        assert palette.name == "pico8"

    def test_get_palette_not_found(self):
        """Test get_palette returns None for unknown palette."""
        palette = get_palette("unknown")
        assert palette is None

    def test_list_palettes(self):
        """Test list_palettes function."""
        names = list_palettes()
        assert "gameboy" in names
        assert "nes" in names
        assert "pico8" in names


class TestEnums:
    """Tests for enum types."""

    def test_pixel_mode_values(self):
        """Test PixelMode enum values."""
        assert PixelMode.PHOTOREALISTIC.value == "photorealistic"
        assert PixelMode.BIT_16.value == "16bit"
        assert PixelMode.BIT_8.value == "8bit"
        assert PixelMode.BIT_1.value == "1bit"

    def test_aspect_ratio_mode_values(self):
        """Test AspectRatioMode enum values."""
        assert AspectRatioMode.PRESERVE.value == "preserve"
        assert AspectRatioMode.STRETCH.value == "stretch"
        assert AspectRatioMode.CROP.value == "crop"

    def test_scaling_filter_values(self):
        """Test ScalingFilter enum values."""
        assert ScalingFilter.NEAREST.value == "nearest"
        assert ScalingFilter.BILINEAR.value == "bilinear"
        assert ScalingFilter.LANCZOS.value == "lanczos"

    def test_dither_mode_values(self):
        """Test DitherMode enum values."""
        assert DitherMode.NONE.value == "none"
        assert DitherMode.ORDERED.value == "ordered"
        assert DitherMode.FLOYD_STEINBERG.value == "floyd_steinberg"
        assert DitherMode.ATKINSON.value == "atkinson"

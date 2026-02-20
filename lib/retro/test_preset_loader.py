"""
Tests for preset_loader module.

Run with: pytest lib/retro/test_preset_loader.py -v
"""

import pytest
from pathlib import Path

from lib.retro.preset_loader import (
    load_pixel_profile,
    list_profiles,
    load_palette,
    list_palettes,
    load_resolution,
    list_resolutions,
    get_snes_config,
    get_nes_config,
    get_gameboy_config,
    get_pico8_config,
)


# Path to test config
CONFIG_PATH = Path(__file__).parent.parent.parent / "configs" / "cinematic" / "retro" / "pixel_profiles.yaml"


class TestLoadPixelProfile:
    """Tests for load_pixel_profile function."""

    def test_load_snes_profile(self):
        """Test loading SNES profile."""
        config = load_pixel_profile("snes", [CONFIG_PATH])
        assert config is not None
        assert config.target_resolution == (256, 224)
        assert config.style.mode == "16bit"
        assert config.style.color_limit == 256

    def test_load_nes_profile(self):
        """Test loading NES profile."""
        config = load_pixel_profile("nes", [CONFIG_PATH])
        assert config is not None
        assert config.target_resolution == (256, 240)
        assert config.style.mode == "8bit"

    def test_load_gameboy_profile(self):
        """Test loading Game Boy profile."""
        config = load_pixel_profile("gameboy", [CONFIG_PATH])
        assert config is not None
        assert config.target_resolution == (160, 144)
        assert config.style.mode == "4bit"
        assert config.palette_name == "gameboy"

    def test_load_pico8_profile(self):
        """Test loading PICO-8 profile."""
        config = load_pixel_profile("pico8", [CONFIG_PATH])
        assert config is not None
        assert config.target_resolution == (128, 128)
        assert config.style.color_limit == 16

    def test_load_mac_plus_profile(self):
        """Test loading Mac Plus profile."""
        config = load_pixel_profile("mac_plus", [CONFIG_PATH])
        assert config is not None
        assert config.style.mode == "1bit"
        assert config.style.dither_mode == "ordered"

    def test_load_nonexistent_profile(self):
        """Test loading non-existent profile returns None."""
        config = load_pixel_profile("nonexistent", [CONFIG_PATH])
        assert config is None

    def test_load_modern_pixel_profile(self):
        """Test loading modern pixel profile."""
        config = load_pixel_profile("modern_pixel", [CONFIG_PATH])
        assert config is not None
        assert config.style.mode == "stylized"


class TestListProfiles:
    """Tests for list_profiles function."""

    def test_list_profiles_includes_common(self):
        """Test that common profiles are listed."""
        profiles = list_profiles([CONFIG_PATH])
        assert "snes" in profiles
        assert "nes" in profiles
        assert "gameboy" in profiles
        assert "pico8" in profiles

    def test_list_profiles_count(self):
        """Test profile count."""
        profiles = list_profiles([CONFIG_PATH])
        assert len(profiles) >= 20  # We have 20+ profiles defined


class TestLoadPalette:
    """Tests for load_palette function."""

    def test_load_gameboy_palette(self):
        """Test loading Game Boy palette."""
        palette = load_palette("gameboy", [CONFIG_PATH])
        assert palette is not None
        assert len(palette.colors) == 4

    def test_load_pico8_palette(self):
        """Test loading PICO-8 palette."""
        palette = load_palette("pico8", [CONFIG_PATH])
        assert palette is not None
        assert len(palette.colors) == 16

    def test_load_cga_palette(self):
        """Test loading CGA palette."""
        palette = load_palette("cga", [CONFIG_PATH])
        assert palette is not None
        assert len(palette.colors) == 4

    def test_load_ega_palette(self):
        """Test loading EGA palette."""
        palette = load_palette("ega", [CONFIG_PATH])
        assert palette is not None
        assert len(palette.colors) == 16

    def test_load_mac_plus_palette(self):
        """Test loading Mac Plus palette."""
        palette = load_palette("mac_plus", [CONFIG_PATH])
        assert palette is not None
        assert len(palette.colors) == 2

    def test_load_nonexistent_palette(self):
        """Test loading non-existent palette returns None."""
        palette = load_palette("nonexistent", [CONFIG_PATH])
        assert palette is None


class TestListPalettes:
    """Tests for list_palettes function."""

    def test_list_palettes_includes_common(self):
        """Test that common palettes are listed."""
        palettes = list_palettes([CONFIG_PATH])
        assert "gameboy" in palettes
        assert "pico8" in palettes

    def test_list_palettes_count(self):
        """Test palette count."""
        palettes = list_palettes([CONFIG_PATH])
        assert len(palettes) >= 6  # We have 6+ palettes defined


class TestLoadResolution:
    """Tests for load_resolution function."""

    def test_load_snes_resolution(self):
        """Test loading SNES resolution."""
        res = load_resolution("snes", [CONFIG_PATH])
        assert res == (256, 224)

    def test_load_nes_resolution(self):
        """Test loading NES resolution."""
        res = load_resolution("nes", [CONFIG_PATH])
        assert res == (256, 240)

    def test_load_gameboy_resolution(self):
        """Test loading Game Boy resolution."""
        res = load_resolution("gameboy", [CONFIG_PATH])
        assert res == (160, 144)

    def test_load_pico8_resolution(self):
        """Test loading PICO-8 resolution."""
        res = load_resolution("pico8", [CONFIG_PATH])
        assert res == (128, 128)

    def test_load_hd_resolution(self):
        """Test loading HD resolution."""
        res = load_resolution("hd", [CONFIG_PATH])
        assert res == (1280, 720)

    def test_load_nonexistent_resolution(self):
        """Test loading non-existent resolution returns None."""
        res = load_resolution("nonexistent", [CONFIG_PATH])
        assert res is None


class TestListResolutions:
    """Tests for list_resolutions function."""

    def test_list_resolutions_includes_common(self):
        """Test that common resolutions are listed."""
        resolutions = list_resolutions([CONFIG_PATH])
        assert "snes" in resolutions
        assert "nes" in resolutions
        assert "hd" in resolutions


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_get_snes_config(self):
        """Test get_snes_config returns valid config."""
        config = get_snes_config()
        assert config is not None
        assert config.style.mode == "16bit"

    def test_get_nes_config(self):
        """Test get_nes_config returns valid config."""
        config = get_nes_config()
        assert config is not None
        assert config.style.mode == "8bit"

    def test_get_gameboy_config(self):
        """Test get_gameboy_config returns valid config."""
        config = get_gameboy_config()
        assert config is not None
        assert config.style.mode == "4bit"

    def test_get_pico8_config(self):
        """Test get_pico8_config returns valid config."""
        config = get_pico8_config()
        assert config is not None
        assert config.style.color_limit == 16

"""
Unit tests for View Preset Loader module
"""

import pytest
from lib.retro.view_preset_loader import (
    load_isometric_preset,
    list_isometric_presets,
    get_isometric_preset,
    load_side_scroller_preset,
    list_side_scroller_presets,
    get_side_scroller_preset,
    load_sprite_sheet_preset,
    list_sprite_sheet_presets,
    get_sprite_sheet_preset,
    load_tile_preset,
    list_tile_presets,
    get_tile_preset,
    load_view_preset,
    list_view_presets,
    clear_preset_cache,
    reload_presets,
)
from lib.retro.isometric_types import (
    IsometricConfig,
    SideScrollerConfig,
    SpriteSheetConfig,
    TileConfig,
)


class TestLoadIsometricPreset:
    """Tests for load_isometric_preset function."""

    def test_load_classic_pixel(self):
        """Test loading classic_pixel preset."""
        config = load_isometric_preset("classic_pixel")
        assert config is not None
        assert isinstance(config, IsometricConfig)
        assert config.angle == "pixel"

    def test_load_strategy(self):
        """Test loading strategy preset."""
        config = load_isometric_preset("strategy")
        assert config is not None
        assert config.angle == "military"

    def test_load_nonexistent(self):
        """Test loading nonexistent preset returns None."""
        config = load_isometric_preset("nonexistent_preset")
        assert config is None


class TestListIsometricPresets:
    """Tests for list_isometric_presets function."""

    def test_returns_list(self):
        """Test returns list."""
        presets = list_isometric_presets()
        assert isinstance(presets, list)

    def test_has_common_presets(self):
        """Test has common presets."""
        presets = list_isometric_presets()
        assert "classic_pixel" in presets

    def test_not_empty(self):
        """Test list is not empty."""
        presets = list_isometric_presets()
        assert len(presets) > 0


class TestGetIsometricPreset:
    """Tests for get_isometric_preset function."""

    def test_returns_config(self):
        """Test returns config even for nonexistent preset."""
        config = get_isometric_preset("nonexistent")
        assert isinstance(config, IsometricConfig)

    def test_returns_preset_if_found(self):
        """Test returns preset config if found."""
        config = get_isometric_preset("classic_pixel")
        assert config.angle == "pixel"


class TestLoadSideScrollerPreset:
    """Tests for load_side_scroller_preset function."""

    def test_load_platformer(self):
        """Test loading platformer preset."""
        config = load_side_scroller_preset("platformer_16bit")
        assert config is not None
        assert isinstance(config, SideScrollerConfig)
        assert config.parallax_layers == 4

    def test_load_simple(self):
        """Test loading simple preset."""
        config = load_side_scroller_preset("simple")
        assert config is not None
        assert config.parallax_layers == 2

    def test_load_nonexistent(self):
        """Test loading nonexistent preset returns None."""
        config = load_side_scroller_preset("nonexistent")
        assert config is None


class TestListSideScrollerPresets:
    """Tests for list_side_scroller_presets function."""

    def test_returns_list(self):
        """Test returns list."""
        presets = list_side_scroller_presets()
        assert isinstance(presets, list)

    def test_has_common_presets(self):
        """Test has common presets."""
        presets = list_side_scroller_presets()
        assert "platformer_16bit" in presets
        assert "simple" in presets


class TestGetSideScrollerPreset:
    """Tests for get_side_scroller_preset function."""

    def test_returns_config(self):
        """Test returns config even for nonexistent preset."""
        config = get_side_scroller_preset("nonexistent")
        assert isinstance(config, SideScrollerConfig)


class TestLoadSpriteSheetPreset:
    """Tests for load_sprite_sheet_preset function."""

    def test_load_character(self):
        """Test loading character preset."""
        config = load_sprite_sheet_preset("character")
        assert config is not None
        assert isinstance(config, SpriteSheetConfig)
        assert config.columns == 8
        assert config.rows == 4

    def test_load_tileset(self):
        """Test loading tileset preset."""
        config = load_sprite_sheet_preset("tileset")
        assert config is not None
        assert config.trim is False  # Tilesets don't trim

    def test_load_nonexistent(self):
        """Test loading nonexistent preset returns None."""
        config = load_sprite_sheet_preset("nonexistent")
        assert config is None


class TestListSpriteSheetPresets:
    """Tests for list_sprite_sheet_presets function."""

    def test_returns_list(self):
        """Test returns list."""
        presets = list_sprite_sheet_presets()
        assert isinstance(presets, list)

    def test_has_common_presets(self):
        """Test has common presets."""
        presets = list_sprite_sheet_presets()
        assert "character" in presets
        assert "tileset" in presets


class TestGetSpriteSheetPreset:
    """Tests for get_sprite_sheet_preset function."""

    def test_returns_config(self):
        """Test returns config even for nonexistent preset."""
        config = get_sprite_sheet_preset("nonexistent")
        assert isinstance(config, SpriteSheetConfig)


class TestLoadTilePreset:
    """Tests for load_tile_preset function."""

    def test_load_nes(self):
        """Test loading NES preset."""
        config = load_tile_preset("nes")
        assert config is not None
        assert isinstance(config, TileConfig)
        assert config.tile_size == (16, 16)

    def test_load_isometric(self):
        """Test loading isometric preset."""
        config = load_tile_preset("isometric_32")
        assert config is not None
        assert config.tile_size == (32, 16)

    def test_load_nonexistent(self):
        """Test loading nonexistent preset returns None."""
        config = load_tile_preset("nonexistent")
        assert config is None


class TestListTilePresets:
    """Tests for list_tile_presets function."""

    def test_returns_list(self):
        """Test returns list."""
        presets = list_tile_presets()
        assert isinstance(presets, list)

    def test_has_common_presets(self):
        """Test has common presets."""
        presets = list_tile_presets()
        assert "nes" in presets
        assert "modern_32" in presets


class TestGetTilePreset:
    """Tests for get_tile_preset function."""

    def test_returns_config(self):
        """Test returns config even for nonexistent preset."""
        config = get_tile_preset("nonexistent")
        assert isinstance(config, TileConfig)


class TestLoadViewPreset:
    """Tests for load_view_preset function."""

    def test_load_isometric(self):
        """Test loading isometric preset."""
        config = load_view_preset("isometric", "classic_pixel")
        assert isinstance(config, IsometricConfig)

    def test_load_side_scroller(self):
        """Test loading side_scroller preset."""
        config = load_view_preset("side_scroller", "simple")
        assert isinstance(config, SideScrollerConfig)

    def test_load_sprite_sheet(self):
        """Test loading sprite_sheet preset."""
        config = load_view_preset("sprite_sheet", "character")
        assert isinstance(config, SpriteSheetConfig)

    def test_load_tile(self):
        """Test loading tile preset."""
        config = load_view_preset("tile", "nes")
        assert isinstance(config, TileConfig)

    def test_invalid_category(self):
        """Test invalid category returns None."""
        config = load_view_preset("invalid_category", "any")
        assert config is None


class TestListViewPresets:
    """Tests for list_view_presets function."""

    def test_returns_all_categories(self):
        """Test returns all categories without filter."""
        presets = list_view_presets()
        assert "isometric" in presets
        assert "side_scroller" in presets
        assert "sprite_sheet" in presets
        assert "tile" in presets

    def test_filter_isometric(self):
        """Test filter to isometric only."""
        presets = list_view_presets("isometric")
        assert "isometric" in presets
        assert len(presets) == 1

    def test_filter_side_scroller(self):
        """Test filter to side_scroller only."""
        presets = list_view_presets("side_scroller")
        assert "side_scroller" in presets

    def test_filter_invalid(self):
        """Test invalid filter returns empty dict."""
        presets = list_view_presets("invalid")
        assert presets == {}


class TestCacheManagement:
    """Tests for cache management functions."""

    def test_clear_and_reload(self):
        """Test clearing and reloading cache."""
        # Load once
        list_isometric_presets()

        # Clear cache
        clear_preset_cache()

        # Reload
        presets = reload_presets()
        assert isinstance(presets, dict)

    def test_clear_cache(self):
        """Test clear_cache doesn't error."""
        clear_preset_cache()  # Should not raise
        clear_preset_cache()  # Call twice to verify


class TestPresetValues:
    """Tests for specific preset values."""

    def test_isometric_blizzard_values(self):
        """Test Blizzard preset has correct values."""
        config = load_isometric_preset("blizzard")
        if config:
            assert config.angle == "blizzard"
            assert config.tile_width == 64
            assert config.tile_height == 32
            assert config.depth_sorting is True

    def test_side_scroller_cinematic_values(self):
        """Test cinematic preset has correct values."""
        config = load_side_scroller_preset("cinematic")
        if config:
            assert config.parallax_layers == 6
            assert len(config.layer_names) == 6

    def test_sprite_sheet_unity_values(self):
        """Test Unity preset has correct format."""
        config = load_sprite_sheet_preset("unity_character")
        if config:
            assert config.json_format == "unity"

    def test_tile_modern_values(self):
        """Test modern_32 preset has correct values."""
        config = load_tile_preset("modern_32")
        if config:
            assert config.tile_size == (32, 32)
            assert config.autotile is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

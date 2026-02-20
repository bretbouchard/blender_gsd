"""
Unit tests for Isometric Types module
"""

import pytest
import math
from lib.retro.isometric_types import (
    IsometricAngle,
    ViewDirection,
    SpriteFormat,
    TileFormat,
    IsometricConfig,
    SideScrollerConfig,
    SpriteSheetConfig,
    TileConfig,
    IsometricRenderResult,
    SpriteSheetResult,
    TileSetResult,
    ISOMETRIC_ANGLES,
    get_isometric_angle,
    list_isometric_angles,
    TILE_SIZES,
    get_tile_size,
    list_tile_sizes,
)


class TestIsometricAngle:
    """Tests for IsometricAngle enum."""

    def test_enum_values(self):
        """Test enum values exist."""
        assert IsometricAngle.TRUE_ISOMETRIC.value == "true_isometric"
        assert IsometricAngle.PIXEL.value == "pixel"
        assert IsometricAngle.MILITARY.value == "military"
        assert IsometricAngle.DIMETRIC.value == "dimetric"


class TestViewDirection:
    """Tests for ViewDirection enum."""

    def test_enum_values(self):
        """Test enum values exist."""
        assert ViewDirection.SIDE.value == "side"
        assert ViewDirection.FRONT.value == "front"
        assert ViewDirection.TOP.value == "top"


class TestSpriteFormat:
    """Tests for SpriteFormat enum."""

    def test_enum_values(self):
        """Test enum values exist."""
        assert SpriteFormat.PHASER.value == "phaser"
        assert SpriteFormat.UNITY.value == "unity"
        assert SpriteFormat.GODOT.value == "godot"
        assert SpriteFormat.GENERIC.value == "generic"


class TestTileFormat:
    """Tests for TileFormat enum."""

    def test_enum_values(self):
        """Test enum values exist."""
        assert TileFormat.PNG.value == "png"
        assert TileFormat.JPG.value == "jpg"
        assert TileFormat.BMP.value == "bmp"
        assert TileFormat.TGA.value == "tga"


class TestIsometricAngles:
    """Tests for ISOMETRIC_ANGLES presets."""

    def test_has_all_angles(self):
        """Test all angle presets exist."""
        assert "true_isometric" in ISOMETRIC_ANGLES
        assert "pixel" in ISOMETRIC_ANGLES
        assert "military" in ISOMETRIC_ANGLES
        assert "dimetric" in ISOMETRIC_ANGLES

    def test_get_isometric_angle(self):
        """Test getting angle preset."""
        angle = get_isometric_angle("pixel")
        assert angle is not None
        assert angle["elevation"] == 30.0
        assert angle["rotation"] == 45.0

    def test_get_isometric_angle_case_insensitive(self):
        """Test angle lookup is case insensitive."""
        angle = get_isometric_angle("PIXEL")
        assert angle is not None

    def test_get_isometric_angle_not_found(self):
        """Test unknown angle returns None."""
        angle = get_isometric_angle("unknown")
        assert angle is None

    def test_list_isometric_angles(self):
        """Test listing angles."""
        angles = list_isometric_angles()
        assert "pixel" in angles
        assert "true_isometric" in angles
        assert len(angles) >= 4


class TestTileSizes:
    """Tests for TILE_SIZES presets."""

    def test_has_common_sizes(self):
        """Test common tile sizes exist."""
        assert "nes" in TILE_SIZES
        assert "snes" in TILE_SIZES
        assert "isometric_32" in TILE_SIZES
        assert "isometric_64" in TILE_SIZES

    def test_get_tile_size(self):
        """Test getting tile size preset."""
        size = get_tile_size("nes")
        assert size == (16, 16)

    def test_get_tile_size_isometric(self):
        """Test getting isometric tile size."""
        size = get_tile_size("isometric_32")
        assert size == (32, 16)

    def test_get_tile_size_not_found(self):
        """Test unknown size returns None."""
        size = get_tile_size("unknown")
        assert size is None

    def test_list_tile_sizes(self):
        """Test listing tile sizes."""
        sizes = list_tile_sizes()
        assert "nes" in sizes
        assert "modern_32" in sizes


class TestIsometricConfig:
    """Tests for IsometricConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = IsometricConfig()
        assert config.enabled is True
        assert config.angle == "pixel"
        assert config.tile_width == 32
        assert config.tile_height == 16
        assert config.depth_sorting is True

    def test_to_dict(self):
        """Test serialization to dictionary."""
        config = IsometricConfig()
        data = config.to_dict()
        assert data["enabled"] is True
        assert data["angle"] == "pixel"
        assert data["tile_width"] == 32

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {"angle": "military", "tile_width": 64}
        config = IsometricConfig.from_dict(data)
        assert config.angle == "military"
        assert config.tile_width == 64

    def test_validate_valid(self):
        """Test validation passes for valid config."""
        config = IsometricConfig()
        errors = config.validate()
        assert len(errors) == 0

    def test_validate_invalid_angle(self):
        """Test validation fails for invalid angle."""
        config = IsometricConfig(angle="invalid")
        errors = config.validate()
        assert len(errors) > 0

    def test_validate_negative_tile_size(self):
        """Test validation fails for negative tile size."""
        config = IsometricConfig(tile_width=-1)
        errors = config.validate()
        assert len(errors) > 0

    def test_get_angles(self):
        """Test getting angles from config."""
        config = IsometricConfig(angle="pixel")
        elevation, rotation = config.get_angles()
        assert elevation == 30.0
        assert rotation == 45.0

    def test_get_angles_custom(self):
        """Test getting custom angles."""
        config = IsometricConfig(
            custom_elevation=25.0,
            custom_rotation=30.0
        )
        elevation, rotation = config.get_angles()
        assert elevation == 25.0
        assert rotation == 30.0

    def test_for_game_style(self):
        """Test game style presets."""
        config = IsometricConfig.for_game_style("classic_pixel")
        assert config.angle == "pixel"
        assert config.tile_width == 64

    def test_for_game_style_unknown(self):
        """Test unknown game style returns default."""
        config = IsometricConfig.for_game_style("unknown")
        assert config.angle == "pixel"  # Default


class TestSideScrollerConfig:
    """Tests for SideScrollerConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = SideScrollerConfig()
        assert config.enabled is True
        assert config.parallax_layers == 4
        assert config.view_direction == "side"
        assert config.orthographic is True

    def test_to_dict(self):
        """Test serialization to dictionary."""
        config = SideScrollerConfig()
        data = config.to_dict()
        assert data["parallax_layers"] == 4
        assert data["view_direction"] == "side"

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {"parallax_layers": 6, "view_direction": "front"}
        config = SideScrollerConfig.from_dict(data)
        assert config.parallax_layers == 6
        assert config.view_direction == "front"

    def test_validate_valid(self):
        """Test validation passes for valid config."""
        config = SideScrollerConfig()
        errors = config.validate()
        assert len(errors) == 0

    def test_validate_invalid_layer_count(self):
        """Test validation fails for invalid layer count."""
        config = SideScrollerConfig(parallax_layers=10)
        errors = config.validate()
        assert len(errors) > 0

    def test_validate_invalid_view_direction(self):
        """Test validation fails for invalid view direction."""
        config = SideScrollerConfig(view_direction="diagonal")
        errors = config.validate()
        assert len(errors) > 0

    def test_get_layer_depth(self):
        """Test getting layer depth."""
        config = SideScrollerConfig()
        depth = config.get_layer_depth(0)
        assert depth == 0.25

    def test_get_layer_name(self):
        """Test getting layer name."""
        config = SideScrollerConfig()
        name = config.get_layer_name(0)
        assert name == "far_bg"

    def test_for_style(self):
        """Test style presets."""
        config = SideScrollerConfig.for_style("platformer_16bit")
        assert config.parallax_layers == 4
        assert "sky" in config.layer_names


class TestSpriteSheetConfig:
    """Tests for SpriteSheetConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = SpriteSheetConfig()
        assert config.columns == 8
        assert config.rows == 8
        assert config.frame_width == 32
        assert config.frame_height == 32
        assert config.trim is True
        assert config.json_format == "phaser"

    def test_to_dict(self):
        """Test serialization to dictionary."""
        config = SpriteSheetConfig()
        data = config.to_dict()
        assert data["columns"] == 8
        assert data["rows"] == 8

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {"columns": 16, "rows": 16, "trim": False}
        config = SpriteSheetConfig.from_dict(data)
        assert config.columns == 16
        assert config.trim is False

    def test_validate_valid(self):
        """Test validation passes for valid config."""
        config = SpriteSheetConfig()
        errors = config.validate()
        assert len(errors) == 0

    def test_validate_invalid_columns(self):
        """Test validation fails for invalid columns."""
        config = SpriteSheetConfig(columns=0)
        errors = config.validate()
        assert len(errors) > 0

    def test_validate_invalid_pivot(self):
        """Test validation fails for invalid pivot."""
        config = SpriteSheetConfig(pivot_x=1.5)
        errors = config.validate()
        assert len(errors) > 0

    def test_get_sheet_size(self):
        """Test calculating sheet size."""
        config = SpriteSheetConfig()
        width, height = config.get_sheet_size()
        assert width == 256  # 8 * 32
        assert height == 256  # 8 * 32

    def test_get_sheet_size_with_spacing(self):
        """Test calculating sheet size with spacing."""
        config = SpriteSheetConfig(spacing=2)
        width, height = config.get_sheet_size()
        assert width == 256 + 7 * 2  # frames + spacing

    def test_for_character(self):
        """Test character preset."""
        config = SpriteSheetConfig.for_character(32, 32)
        assert config.columns == 8
        assert config.rows == 4

    def test_for_tileset(self):
        """Test tileset preset."""
        config = SpriteSheetConfig.for_tileset(16)
        assert config.columns == 16
        assert config.power_of_two is True


class TestTileConfig:
    """Tests for TileConfig dataclass."""

    def test_default_values(self):
        """Test default configuration values."""
        config = TileConfig()
        assert config.tile_size == (32, 32)
        assert config.format == "png"
        assert config.generate_map is True

    def test_to_dict(self):
        """Test serialization to dictionary."""
        config = TileConfig()
        data = config.to_dict()
        assert data["tile_size"] == [32, 32]

    def test_from_dict(self):
        """Test deserialization from dictionary."""
        data = {"tile_size": [64, 64], "format": "jpg"}
        config = TileConfig.from_dict(data)
        assert config.tile_size == (64, 64)
        assert config.format == "jpg"

    def test_validate_valid(self):
        """Test validation passes for valid config."""
        config = TileConfig()
        errors = config.validate()
        assert len(errors) == 0

    def test_validate_invalid_tile_size(self):
        """Test validation fails for invalid tile size."""
        config = TileConfig(tile_size=(0, 0))
        errors = config.validate()
        assert len(errors) > 0

    def test_for_console(self):
        """Test console preset."""
        config = TileConfig.for_console("nes")
        assert config.tile_size == (16, 16)

    def test_for_isometric(self):
        """Test isometric preset."""
        config = TileConfig.for_isometric("pixel")
        assert config.tile_size == (32, 16)


class TestResultTypes:
    """Tests for result dataclasses."""

    def test_isometric_render_result(self):
        """Test IsometricRenderResult."""
        result = IsometricRenderResult()
        assert result.tile_count == 0
        data = result.to_dict()
        assert "tile_count" in data

    def test_sprite_sheet_result(self):
        """Test SpriteSheetResult."""
        result = SpriteSheetResult()
        assert result.frame_count == 0
        data = result.to_dict()
        assert "frame_count" in data

    def test_tile_set_result(self):
        """Test TileSetResult."""
        result = TileSetResult()
        assert result.tile_count == 0
        data = result.to_dict()
        assert "tile_count" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Unit tests for Sprite Sheet module
"""

import pytest
import math
from lib.retro.sprites import (
    SpriteFrame,
    generate_sprite_sheet,
    trim_sprite,
    calculate_pivot,
    calculate_pivot_world,
    generate_sprite_metadata,
    export_phaser_json,
    export_unity_json,
    export_godot_json,
    export_generic_json,
    get_frame_position,
    get_frame_bounds,
    calculate_frame_count,
    optimize_sheet_layout,
)
from lib.retro.isometric_types import SpriteSheetConfig


class TestSpriteFrame:
    """Tests for SpriteFrame dataclass."""

    def test_default_values(self):
        """Test default values."""
        frame = SpriteFrame()
        assert frame.x == 0
        assert frame.y == 0
        assert frame.width == 0
        assert frame.height == 0
        assert frame.trimmed is False

    def test_to_dict(self):
        """Test serialization."""
        frame = SpriteFrame(x=10, y=20, width=32, height=32)
        data = frame.to_dict()
        assert data["x"] == 10
        assert data["y"] == 20
        assert data["width"] == 32
        assert data["height"] == 32


class TestGenerateSpriteSheet:
    """Tests for generate_sprite_sheet function."""

    def test_empty_images(self):
        """Test empty image list."""
        config = SpriteSheetConfig()
        result = generate_sprite_sheet([], config)
        assert result.frame_count == 0
        assert "No images provided" in result.warnings

    def test_returns_result(self):
        """Test returns SpriteSheetResult."""
        config = SpriteSheetConfig()
        result = generate_sprite_sheet([], config)
        assert hasattr(result, 'frame_count')
        assert hasattr(result, 'metadata')
        assert hasattr(result, 'warnings')


class TestTrimSprite:
    """Tests for trim_sprite function."""

    def test_returns_tuple(self):
        """Test returns tuple of (image, bounds)."""
        try:
            from PIL import Image

            img = Image.new('RGBA', (32, 32), (255, 0, 0, 255))
            trimmed, bounds = trim_sprite(img)
            assert trimmed is not None
            assert len(bounds) == 4
        except ImportError:
            pytest.skip("PIL not available")

    def test_fully_transparent(self):
        """Test fully transparent image."""
        try:
            from PIL import Image

            img = Image.new('RGBA', (32, 32), (0, 0, 0, 0))
            trimmed, bounds = trim_sprite(img)
            # Bounds should match original size
            assert bounds == (0, 0, 32, 32)
        except ImportError:
            pytest.skip("PIL not available")


class TestCalculatePivot:
    """Tests for calculate_pivot function."""

    def test_returns_tuple(self):
        """Test returns tuple."""
        config = SpriteSheetConfig(pivot_x=0.5, pivot_y=0.5)
        try:
            from PIL import Image

            img = Image.new('RGBA', (32, 32), (255, 0, 0, 255))
            pivot = calculate_pivot(img, (0, 0, 0, 0), config)
            assert len(pivot) == 2
            assert pivot[0] == 0.5
            assert pivot[1] == 0.5
        except ImportError:
            pytest.skip("PIL not available")


class TestCalculatePivotWorld:
    """Tests for calculate_pivot_world function."""

    def test_no_trim(self):
        """Test pivot with no trimming."""
        config = SpriteSheetConfig(pivot_x=0.5, pivot_y=0.5)
        pivot = calculate_pivot_world((0, 0, 0, 0), (32, 32), config)
        assert pivot[0] == 0.5
        assert pivot[1] == 0.5

    def test_with_trim(self):
        """Test pivot adjusted for trim."""
        config = SpriteSheetConfig(pivot_x=0.5, pivot_y=0.5)
        # Trim 4 pixels from left, 4 from top, 4 from right, 4 from bottom
        # Original: 32x32, Trimmed: 24x24
        pivot = calculate_pivot_world((4, 4, 4, 4), (32, 32), config)
        # Pivot should be adjusted
        assert 0 <= pivot[0] <= 1
        assert 0 <= pivot[1] <= 1


class TestGenerateSpriteMetadata:
    """Tests for generate_sprite_metadata function."""

    def test_phaser_format(self):
        """Test Phaser format generation."""
        config = SpriteSheetConfig(json_format="phaser")
        frames = [SpriteFrame(x=0, y=0, width=32, height=32)]
        metadata = generate_sprite_metadata(None, config, frames)
        assert "frames" in metadata
        assert "meta" in metadata

    def test_unity_format(self):
        """Test Unity format generation."""
        config = SpriteSheetConfig(json_format="unity")
        frames = [SpriteFrame(x=0, y=0, width=32, height=32)]
        metadata = generate_sprite_metadata(None, config, frames)
        assert "sprites" in metadata

    def test_godot_format(self):
        """Test Godot format generation."""
        config = SpriteSheetConfig(json_format="godot")
        frames = [SpriteFrame(x=0, y=0, width=32, height=32)]
        metadata = generate_sprite_metadata(None, config, frames)
        assert "frames" in metadata
        assert "meta" in metadata

    def test_generic_format(self):
        """Test generic format generation."""
        config = SpriteSheetConfig(json_format="generic")
        frames = [SpriteFrame(x=0, y=0, width=32, height=32)]
        metadata = generate_sprite_metadata(None, config, frames)
        assert "frames" in metadata
        assert "config" in metadata


class TestExportPhaserJson:
    """Tests for export_phaser_json function."""

    def test_structure(self):
        """Test Phaser JSON structure."""
        config = SpriteSheetConfig()
        frames = [
            SpriteFrame(x=0, y=0, width=32, height=32),
            SpriteFrame(x=32, y=0, width=32, height=32),
        ]
        data = export_phaser_json(config, frames)
        assert "frames" in data
        assert "meta" in data
        assert "frame_0" in data["frames"]
        assert "frame_1" in data["frames"]

    def test_frame_data(self):
        """Test frame data structure."""
        config = SpriteSheetConfig()
        frames = [SpriteFrame(x=0, y=0, width=32, height=32, trimmed=True)]
        data = export_phaser_json(config, frames)
        frame_data = data["frames"]["frame_0"]
        assert "frame" in frame_data
        assert "rotated" in frame_data
        assert "trimmed" in frame_data
        assert frame_data["trimmed"] is True


class TestExportUnityJson:
    """Tests for export_unity_json function."""

    def test_structure(self):
        """Test Unity JSON structure."""
        config = SpriteSheetConfig()
        frames = [SpriteFrame(x=0, y=0, width=32, height=32)]
        data = export_unity_json(config, frames)
        assert "name" in data
        assert "sprites" in data
        assert len(data["sprites"]) == 1

    def test_sprite_data(self):
        """Test sprite data structure."""
        config = SpriteSheetConfig()
        frames = [SpriteFrame(x=0, y=0, width=32, height=32, pivot=(0.5, 1.0))]
        data = export_unity_json(config, frames)
        sprite = data["sprites"][0]
        assert "name" in sprite
        assert "x" in sprite
        assert "pivotX" in sprite
        assert sprite["pivotX"] == 0.5


class TestExportGodotJson:
    """Tests for export_godot_json function."""

    def test_structure(self):
        """Test Godot JSON structure."""
        config = SpriteSheetConfig()
        frames = [SpriteFrame(x=0, y=0, width=32, height=32)]
        data = export_godot_json(config, frames)
        assert "frames" in data
        assert "meta" in data
        assert len(data["frames"]) == 1

    def test_frame_has_duration(self):
        """Test frames have duration field."""
        config = SpriteSheetConfig()
        frames = [SpriteFrame(x=0, y=0, width=32, height=32)]
        data = export_godot_json(config, frames)
        assert "duration" in data["frames"][0]


class TestExportGenericJson:
    """Tests for export_generic_json function."""

    def test_structure(self):
        """Test generic JSON structure."""
        config = SpriteSheetConfig()
        frames = [SpriteFrame(x=0, y=0, width=32, height=32)]
        data = export_generic_json(config, frames)
        assert "frames" in data
        assert "sheet_size" in data
        assert "config" in data

    def test_includes_config(self):
        """Test includes original config."""
        config = SpriteSheetConfig(columns=16, rows=16)
        frames = [SpriteFrame(x=0, y=0, width=32, height=32)]
        data = export_generic_json(config, frames)
        assert data["config"]["columns"] == 16


class TestGetFramePosition:
    """Tests for get_frame_position function."""

    def test_first_frame(self):
        """Test first frame position."""
        config = SpriteSheetConfig(padding=0, spacing=0)
        x, y = get_frame_position(0, config)
        assert x == 0
        assert y == 0

    def test_with_padding(self):
        """Test position with padding."""
        config = SpriteSheetConfig(padding=4, spacing=0)
        x, y = get_frame_position(0, config)
        assert x == 4
        assert y == 4

    def test_second_column(self):
        """Test second column position."""
        config = SpriteSheetConfig(frame_width=32, spacing=0, padding=0)
        x, y = get_frame_position(1, config)
        assert x == 32

    def test_with_spacing(self):
        """Test position with spacing."""
        config = SpriteSheetConfig(frame_width=32, spacing=2, padding=0)
        x, y = get_frame_position(1, config)
        assert x == 32 + 2

    def test_second_row(self):
        """Test second row position."""
        config = SpriteSheetConfig(columns=8, frame_width=32, frame_height=32, spacing=0, padding=0)
        x, y = get_frame_position(8, config)  # First frame of second row
        assert x == 0
        assert y == 32


class TestGetFrameBounds:
    """Tests for get_frame_bounds function."""

    def test_returns_tuple(self):
        """Test returns 4-element tuple."""
        config = SpriteSheetConfig()
        bounds = get_frame_bounds(0, config)
        assert len(bounds) == 4
        x, y, w, h = bounds
        assert w == config.frame_width
        assert h == config.frame_height


class TestCalculateFrameCount:
    """Tests for calculate_frame_count function."""

    def test_calculates_correctly(self):
        """Test calculates total frames."""
        config = SpriteSheetConfig(columns=8, rows=4)
        count = calculate_frame_count(config)
        assert count == 32

    def test_large_sheet(self):
        """Test large sheet calculation."""
        config = SpriteSheetConfig(columns=16, rows=16)
        count = calculate_frame_count(config)
        assert count == 256


class TestOptimizeSheetLayout:
    """Tests for optimize_sheet_layout function."""

    def test_single_frame(self):
        """Test single frame."""
        cols, rows = optimize_sheet_layout(1, 32, 32)
        assert cols == 1
        assert rows == 1

    def test_four_frames(self):
        """Test four frames - should be square."""
        cols, rows = optimize_sheet_layout(4, 32, 32)
        assert cols == 2
        assert rows == 2

    def test_respects_max_size(self):
        """Test respects maximum size."""
        # Smaller frame count that fits within max size
        cols, rows = optimize_sheet_layout(16, 32, 32, max_size=(128, 128))
        # 128 / 32 = 4 max columns
        assert cols <= 4
        assert rows <= 4


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

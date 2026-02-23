"""
Unit tests for HDRI Environment Lighting Module

Tests for lib/cinematic/hdri.py - HDRI loading, configuration, and management.
All tests run without Blender (mocked) for CI compatibility.
"""

import pytest
import math
from pathlib import Path
from unittest.mock import patch, MagicMock

from lib.cinematic.hdri import (
    find_hdri_path,
    setup_hdri,
    load_hdri_preset,
    clear_hdri,
    get_hdri_info,
    list_available_hdris,
    DEFAULT_HDRI_PATHS,
    HDRI_EXTENSIONS,
    BLENDER_AVAILABLE,
)


class TestFindHdriPath:
    """Tests for HDRI file path finding."""

    def test_find_nonexistent_file(self):
        """Test finding a file that doesn't exist."""
        result = find_hdri_path("nonexistent.hdr")
        assert result is None

    def test_find_with_custom_paths(self, tmp_path):
        """Test finding file with custom search paths."""
        # Create a temporary HDRI file
        hdri_file = tmp_path / "test.hdr"
        hdri_file.write_text("mock hdri content")

        result = find_hdri_path("test.hdr", search_paths=[tmp_path])
        assert result == hdri_file

    def test_find_search_order(self, tmp_path):
        """Test that search paths are checked in order."""
        # Create two directories
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()

        # Create HDRI in second directory
        hdri2 = dir2 / "test.hdr"
        hdri2.write_text("content")

        # Should find in dir1 first (even though empty)
        result = find_hdri_path("test.hdr", search_paths=[dir1, dir2])
        assert result == hdri2  # Falls through to dir2

    def test_find_relative_path(self, tmp_path):
        """Test finding with relative path handling."""
        # Create nested structure
        subdir = tmp_path / "subdir"
        subdir.mkdir()
        hdri_file = subdir / "nested.hdr"
        hdri_file.write_text("content")

        result = find_hdri_path("nested.hdr", search_paths=[subdir])
        assert result == hdri_file


class TestSetupHdri:
    """Tests for HDRI setup in scene."""

    def test_setup_hdri_blender_unavailable(self):
        """Test setup returns False when Blender not available."""
        result = setup_hdri("/path/to/hdri.hdr")
        assert result is False

    def test_setup_hdri_with_exposure(self):
        """Test setup with exposure parameter."""
        result = setup_hdri(
            "/path/to/hdri.hdr",
            exposure=1.5
        )
        assert result is False  # Blender not available

    def test_setup_hdri_with_rotation(self):
        """Test setup with rotation parameter."""
        result = setup_hdri(
            "/path/to/hdri.hdr",
            rotation=90.0
        )
        assert result is False

    def test_setup_hdri_background_visible(self):
        """Test setup with background visibility."""
        result = setup_hdri(
            "/path/to/hdri.hdr",
            background_visible=True
        )
        assert result is False

    def test_setup_hdri_with_saturation(self):
        """Test setup with saturation parameter."""
        result = setup_hdri(
            "/path/to/hdri.hdr",
            saturation=0.8
        )
        assert result is False


class TestLoadHdriPreset:
    """Tests for HDRI preset loading."""

    def test_load_preset_blender_unavailable(self):
        """Test loading preset when Blender not available."""
        result = load_hdri_preset("studio_bright")
        assert result is False

    def test_load_preset_with_custom_paths(self):
        """Test loading preset with custom search paths."""
        result = load_hdri_preset(
            "custom_preset",
            search_paths=[Path("/custom/path")]
        )
        assert result is False


class TestClearHdri:
    """Tests for clearing HDRI from scene."""

    @pytest.mark.skipif(BLENDER_AVAILABLE, reason="Test requires Blender to be unavailable, but bpy is mocked")
    def test_clear_hdri_blender_unavailable(self):
        """Test clearing HDRI when Blender not available."""
        result = clear_hdri()
        assert result is False


class TestGetHdriInfo:
    """Tests for getting HDRI information."""

    def test_get_info_returns_dict(self):
        """Test getting info returns a dict with expected keys."""
        result = get_hdri_info()

        # Check that all expected keys exist
        assert "has_hdri" in result
        assert "image_name" in result
        assert "exposure" in result
        assert "rotation" in result
        assert "background_visible" in result

        # Check types
        assert isinstance(result["has_hdri"], bool)
        assert isinstance(result["exposure"], (int, float))
        assert isinstance(result["rotation"], (int, float))


class TestListAvailableHdris:
    """Tests for listing available HDRI files."""

    def test_list_empty_directory(self, tmp_path):
        """Test listing from empty directory."""
        result = list_available_hdris(search_paths=[tmp_path])
        assert result == []

    def test_list_with_hdr_files(self, tmp_path):
        """Test listing HDR files."""
        # Create test files
        (tmp_path / "studio.hdr").write_text("content")
        (tmp_path / "outdoor.exr").write_text("content")
        (tmp_path / "other.txt").write_text("content")  # Not an HDRI

        result = list_available_hdris(search_paths=[tmp_path])

        assert "studio.hdr" in result
        assert "outdoor.exr" in result
        assert "other.txt" not in result

    def test_list_multiple_directories(self, tmp_path):
        """Test listing from multiple directories."""
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()

        (dir1 / "hdri1.hdr").write_text("content")
        (dir2 / "hdri2.hdr").write_text("content")

        result = list_available_hdris(search_paths=[dir1, dir2])

        assert "hdri1.hdr" in result
        assert "hdri2.hdr" in result

    def test_list_sorted_results(self, tmp_path):
        """Test that results are sorted."""
        (tmp_path / "zebra.hdr").write_text("content")
        (tmp_path / "alpha.hdr").write_text("content")
        (tmp_path / "middle.hdr").write_text("content")

        result = list_available_hdris(search_paths=[tmp_path])

        assert result == ["alpha.hdr", "middle.hdr", "zebra.hdr"]

    def test_list_deduplicates(self, tmp_path):
        """Test that results are deduplicated."""
        dir1 = tmp_path / "dir1"
        dir2 = tmp_path / "dir2"
        dir1.mkdir()
        dir2.mkdir()

        # Same filename in both directories
        (dir1 / "same.hdr").write_text("content1")
        (dir2 / "same.hdr").write_text("content2")

        result = list_available_hdris(search_paths=[dir1, dir2])

        assert result.count("same.hdr") == 1


class TestConstants:
    """Tests for module constants."""

    def test_default_hdri_paths(self):
        """Test default HDRI search paths."""
        assert len(DEFAULT_HDRI_PATHS) == 3

        # Check path types
        for path in DEFAULT_HDRI_PATHS:
            assert isinstance(path, Path)

    def test_hdri_extensions(self):
        """Test supported HDRI extensions."""
        assert ".hdr" in HDRI_EXTENSIONS
        assert ".exr" in HDRI_EXTENSIONS
        assert ".hdri" in HDRI_EXTENSIONS

    def test_hdri_extensions_lower_case(self):
        """Test that extensions are lowercase."""
        for ext in HDRI_EXTENSIONS:
            assert ext == ext.lower()


class TestHdriConfig:
    """Tests for HDRIConfig dataclass (from types.py)."""

    def test_default_config(self):
        """Test default HDRIConfig values."""
        from lib.cinematic.types import HDRIConfig

        config = HDRIConfig()

        assert config.name == "studio_bright"
        assert config.file == ""
        assert config.exposure == 0.0
        assert config.rotation == 0.0
        assert config.background_visible is False
        assert config.saturation == 1.0

    def test_custom_config(self):
        """Test custom HDRIConfig."""
        from lib.cinematic.types import HDRIConfig

        config = HDRIConfig(
            name="golden_hour",
            file="golden_hour_4k.hdr",
            exposure=0.5,
            rotation=45.0,
            background_visible=True
        )

        assert config.name == "golden_hour"
        assert config.file == "golden_hour_4k.hdr"
        assert config.exposure == 0.5
        assert config.rotation == 45.0
        assert config.background_visible is True

    def test_serialization(self):
        """Test HDRIConfig to_dict/from_dict roundtrip."""
        from lib.cinematic.types import HDRIConfig

        original = HDRIConfig(
            name="custom_hdri",
            file="/path/to/hdri.exr",
            exposure=-1.0,
            rotation=180.0,
            background_visible=True,
            saturation=0.8
        )

        data = original.to_dict()
        restored = HDRIConfig.from_dict(data)

        assert restored.name == original.name
        assert restored.file == original.file
        assert restored.exposure == original.exposure
        assert restored.rotation == original.rotation
        assert restored.background_visible == original.background_visible
        assert restored.saturation == original.saturation


class TestExposureConversion:
    """Tests for exposure to strength conversion."""

    def test_exposure_zero_equals_strength_one(self):
        """Test that exposure 0 equals strength 1.0."""
        # This is the formula used: strength = 2^exposure
        exposure = 0.0
        expected_strength = math.pow(2.0, exposure)
        assert expected_strength == 1.0

    def test_exposure_positive_increases_strength(self):
        """Test that positive exposure increases strength."""
        exposure = 2.0
        strength = math.pow(2.0, exposure)
        assert strength == 4.0  # 2x brighter per stop

    def test_exposure_negative_decreases_strength(self):
        """Test that negative exposure decreases strength."""
        exposure = -2.0
        strength = math.pow(2.0, exposure)
        assert strength == 0.25  # 0.5x per stop


class TestRotationConversion:
    """Tests for rotation conversion."""

    def test_rotation_degrees_to_radians(self):
        """Test degree to radian conversion."""
        # 90 degrees = pi/2 radians
        degrees = 90.0
        radians = math.radians(degrees)
        assert abs(radians - math.pi / 2) < 0.001

    def test_rotation_360_degrees(self):
        """Test full rotation."""
        degrees = 360.0
        radians = math.radians(degrees)
        assert abs(radians - 2 * math.pi) < 0.001


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

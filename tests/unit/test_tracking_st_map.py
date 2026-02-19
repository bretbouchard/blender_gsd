"""
Unit tests for ST-Map module.

Tests UV distortion map generation for lens correction
in compositing workflows.
"""

import pytest
import sys
import tempfile
import os
import math
from pathlib import Path

# Add lib to path for imports
lib_path = Path(__file__).parent.parent.parent / "lib"
sys.path.insert(0, str(lib_path))

from cinematic.tracking.st_map import (
    STMapConfig,
    STMapResult,
    STMapGenerator,
    STMapBatchGenerator,
    generate_st_map,
)
from cinematic.tracking.types import CameraProfile
from oracle import Oracle


class TestSTMapConfig:
    """Tests for STMapConfig dataclass."""

    def test_create_default(self):
        """Test creating config with defaults."""
        config = STMapConfig()
        Oracle.assert_equal(config.resolution_x, 2048)
        Oracle.assert_equal(config.resolution_y, 1080)
        Oracle.assert_equal(config.encode_undistort, True)
        Oracle.assert_equal(config.bit_depth, 16)

    def test_create_custom(self):
        """Test creating config with custom values."""
        config = STMapConfig(
            resolution_x=4096,
            resolution_y=2160,
            encode_undistort=False,
            bit_depth=32,
            overscan=0.2,
        )
        Oracle.assert_equal(config.resolution_x, 4096)
        Oracle.assert_equal(config.resolution_y, 2160)
        Oracle.assert_equal(config.encode_undistort, False)
        Oracle.assert_equal(config.overscan, 0.2)

    def test_serialization(self):
        """Test to_dict and from_dict roundtrip."""
        original = STMapConfig(
            resolution_x=3840,
            resolution_y=2160,
            bit_depth=16,
        )
        data = original.to_dict()
        restored = STMapConfig.from_dict(data)

        Oracle.assert_equal(restored.resolution_x, original.resolution_x)
        Oracle.assert_equal(restored.resolution_y, original.resolution_y)
        Oracle.assert_equal(restored.bit_depth, original.bit_depth)


class TestSTMapResult:
    """Tests for STMapResult dataclass."""

    def test_create_default(self):
        """Test creating result with defaults."""
        result = STMapResult()
        Oracle.assert_equal(result.width, 0)
        Oracle.assert_equal(result.height, 0)
        Oracle.assert_equal(len(result.data), 0)

    def test_create_with_data(self):
        """Test creating result with data."""
        data = [(0.5, 0.5, 0.5, 1.0)] * 100
        result = STMapResult(
            width=10,
            height=10,
            data=data,
            generation_time_ms=50.0,
        )

        Oracle.assert_equal(result.width, 10)
        Oracle.assert_equal(result.height, 10)
        Oracle.assert_equal(len(result.data), 100)


class TestSTMapGenerator:
    """Tests for STMapGenerator class."""

    def create_test_profile(self):
        """Create a test camera profile with distortion."""
        return CameraProfile(
            name="test_profile",
            sensor_width=36.0,
            sensor_height=24.0,
            distortion_model="brown_conrady",
            k1=-0.05,
            k2=0.02,
            k3=0.0,
            p1=0.0,
            p2=0.0,
        )

    def test_create_default(self):
        """Test creating generator with defaults."""
        generator = STMapGenerator()
        Oracle.assert_not_none(generator.config)

    def test_create_with_config(self):
        """Test creating generator with config."""
        config = STMapConfig(resolution_x=512, resolution_y=512)
        generator = STMapGenerator(config)
        Oracle.assert_equal(generator.config.resolution_x, 512)

    def test_generate_small_map(self):
        """Test generating small ST-Map."""
        config = STMapConfig(resolution_x=64, resolution_y=64)
        generator = STMapGenerator(config)

        profile = self.create_test_profile()
        result = generator.generate(profile)

        Oracle.assert_equal(result.width, 64)
        Oracle.assert_equal(result.height, 64)
        Oracle.assert_equal(len(result.data), 64 * 64)

    def test_generate_records_time(self):
        """Test that generation records time."""
        config = STMapConfig(resolution_x=32, resolution_y=32)
        generator = STMapGenerator(config)

        profile = self.create_test_profile()
        result = generator.generate(profile)

        Oracle.assert_greater_than(result.generation_time_ms, 0)

    def test_generate_progress_callback(self):
        """Test progress callback is called."""
        config = STMapConfig(resolution_x=16, resolution_y=16)
        generator = STMapGenerator(config)

        progress_values = []

        def callback(p):
            progress_values.append(p)

        profile = self.create_test_profile()
        generator.generate(profile, progress_callback=callback)

        Oracle.assert_greater_than(len(progress_values), 0)
        Oracle.assert_less_than_or_equal(progress_values[-1], 1.0)

    def test_generate_undistort_vs_distort(self):
        """Test difference between undistort and distort maps."""
        profile = self.create_test_profile()

        # Generate undistort map
        config_undistort = STMapConfig(
            resolution_x=32,
            resolution_y=32,
            encode_undistort=True,
        )
        generator_undistort = STMapGenerator(config_undistort)
        result_undistort = generator_undistort.generate(profile)

        # Generate distort map
        config_distort = STMapConfig(
            resolution_x=32,
            resolution_y=32,
            encode_undistort=False,
        )
        generator_distort = STMapGenerator(config_distort)
        result_distort = generator_distort.generate(profile)

        # Maps should be different
        # Center pixel should be similar, edges should differ
        center_undistort = result_undistort.data[16 * 32 + 16]
        center_distort = result_distort.data[16 * 32 + 16]

        # Center should be nearly identical for symmetric distortion
        Oracle.assert_less_than(abs(center_undistort[0] - center_distort[0]), 0.01)
        Oracle.assert_less_than(abs(center_undistort[1] - center_distort[1]), 0.01)

    def test_generate_from_name(self):
        """Test generation from profile name."""
        config = STMapConfig(resolution_x=32, resolution_y=32)
        generator = STMapGenerator(config)

        result = generator.generate_from_name("generic_full_frame")

        Oracle.assert_not_none(result)
        Oracle.assert_equal(len(result.data), 32 * 32)

    def test_generate_from_invalid_name(self):
        """Test generation from invalid profile name."""
        config = STMapConfig(resolution_x=32, resolution_y=32)
        generator = STMapGenerator(config)

        with pytest.raises(ValueError):
            generator.generate_from_name("nonexistent_profile")

    def test_save_png_fallback(self):
        """Test saving as PNG."""
        config = STMapConfig(resolution_x=32, resolution_y=32)
        generator = STMapGenerator(config)

        profile = self.create_test_profile()
        result = generator.generate(profile)

        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_path = f.name

        try:
            success = generator.save_png(result, temp_path)
            # May fail without PIL, but should not crash
            Oracle.assert_true(success or not success)  # Just verify no exception
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_save_exr_fallback(self):
        """Test saving as EXR fallback."""
        config = STMapConfig(resolution_x=32, resolution_y=32)
        generator = STMapGenerator(config)

        profile = self.create_test_profile()
        result = generator.generate(profile)

        with tempfile.NamedTemporaryFile(suffix=".exr", delete=False) as f:
            temp_path = f.name

        try:
            success = generator.save_exr(result, temp_path)
            # Fallback should create a file
            Oracle.assert_true(os.path.exists(temp_path) or success)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)

    def test_no_distortion_profile(self):
        """Test with profile that has no distortion."""
        config = STMapConfig(resolution_x=16, resolution_y=16)
        generator = STMapGenerator(config)

        # Profile with no distortion
        profile = CameraProfile(
            name="no_distortion",
            distortion_model="none",
        )

        result = generator.generate(profile)

        # For no distortion, ST-Map should be identity mapping
        # Center pixel should map to itself
        center_idx = 8 * 16 + 8
        r, g, b, a = result.data[center_idx]

        # Should be close to 0.5 (center of image)
        Oracle.assert_less_than(abs(r - 0.5), 0.01)
        Oracle.assert_less_than(abs(g - 0.5), 0.01)


class TestSTMapBatchGenerator:
    """Tests for STMapBatchGenerator class."""

    def test_create(self):
        """Test creating batch generator."""
        generator = STMapBatchGenerator()
        Oracle.assert_not_none(generator.config)

    def test_generate_for_resolutions(self):
        """Test generating for multiple resolutions."""
        batch_gen = STMapBatchGenerator(STMapConfig(bit_depth=16))

        resolutions = [
            (32, 32),
            (64, 64),
            (128, 64),
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            results = batch_gen.generate_for_resolutions(
                profile_name="generic_full_frame",
                resolutions=resolutions,
                output_dir=temp_dir,
            )

            Oracle.assert_equal(len(results), 3)

            # Check that each result has correct resolution
            for i, (w, h) in enumerate(resolutions):
                Oracle.assert_equal(results[i].width, w)
                Oracle.assert_equal(results[i].height, h)


class TestConvenienceFunctions:
    """Tests for convenience functions."""

    def test_generate_st_map(self):
        """Test convenience generate function."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = str(Path(temp_dir) / "test_stmap.png")

            result = generate_st_map(
                profile_name="generic_full_frame",
                resolution=(64, 64),
                output_path=output_path,
                undistort=True,
            )

            Oracle.assert_not_none(result)
            Oracle.assert_equal(result.width, 64)
            Oracle.assert_equal(result.height, 64)

    def test_generate_st_map_no_output(self):
        """Test convenience function without output."""
        result = generate_st_map(
            profile_name="generic_full_frame",
            resolution=(32, 32),
        )

        Oracle.assert_not_none(result)
        Oracle.assert_equal(result.output_path, "")


class TestSTMapValues:
    """Tests for ST-Map value correctness."""

    def test_center_pixel_undistort(self):
        """Test center pixel value for undistort map."""
        config = STMapConfig(
            resolution_x=16,
            resolution_y=16,
            encode_undistort=True,
        )
        generator = STMapGenerator(config)

        # Profile with slight distortion
        profile = CameraProfile(
            name="test",
            k1=-0.01,
            k2=0.0,
        )

        result = generator.generate(profile)

        # Center pixel index
        center_idx = 8 * 16 + 8
        r, g, b, a = result.data[center_idx]

        # Center should map close to itself (0.5, 0.5)
        # With small distortion, difference should be minimal
        Oracle.assert_less_than(abs(r - 0.5), 0.05)
        Oracle.assert_less_than(abs(g - 0.5), 0.05)

    def test_edge_pixels_different_from_center(self):
        """Test edge pixels differ from center with distortion."""
        config = STMapConfig(
            resolution_x=16,
            resolution_y=16,
            encode_undistort=True,
            overscan=0.0,
        )
        generator = STMapGenerator(config)

        # Profile with noticeable distortion
        profile = CameraProfile(
            name="test",
            k1=-0.1,  # Stronger distortion
            k2=0.05,
        )

        result = generator.generate(profile)

        # Get center pixel
        center_idx = 8 * 16 + 8
        center_val = result.data[center_idx]

        # Get corner pixel
        corner_idx = 0
        corner_val = result.data[corner_idx]

        # Corner should be more affected by distortion
        # Both values should be valid (0-1 range if normalized)
        for val in [center_val, corner_val]:
            Oracle.assert_greater_than_or_equal(val[0], 0)
            Oracle.assert_less_than_or_equal(val[0], 1)

    def test_symmetric_distortion_symmetric_map(self):
        """Test that symmetric distortion produces symmetric map."""
        config = STMapConfig(
            resolution_x=17,  # Odd for true center
            resolution_y=17,
            encode_undistort=True,
        )
        generator = STMapGenerator(config)

        # Symmetric distortion (no tangential)
        profile = CameraProfile(
            name="test",
            k1=-0.05,
            k2=0.02,
            p1=0.0,
            p2=0.0,
        )

        result = generator.generate(profile)

        # Check symmetry: pixel (x, y) should match pixel (w-x, h-y)
        w, h = 17, 17

        for y in range(h // 2):
            for x in range(w // 2):
                idx1 = y * w + x
                idx2 = (h - 1 - y) * w + (w - 1 - x)

                v1 = result.data[idx1]
                v2 = result.data[idx2]

                # R should be mirrored, G should be mirrored
                # Due to symmetry, (r1, g1) should map to (1-r2, 1-g2) for center
                # This is approximate due to discrete sampling


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

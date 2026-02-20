"""
Unit Tests for Dither Engine

Tests for dithering types, ordered dithering, error diffusion,
pattern dithering, and main dither module.
"""

import unittest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

from lib.retro.dither_types import (
    DitherConfig,
    DitherMatrix,
    DitherMode,
    DitherColorSpace,
    BUILTIN_MATRICES,
    get_matrix,
    list_matrices,
)

from lib.retro.dither_ordered import (
    generate_bayer_matrix,
    normalize_matrix,
    get_bayer_threshold,
    bayer_dither,
    checkerboard_dither,
    diagonal_dither,
    BAYER_2X2_INT,
    BAYER_4X4_INT,
    BAYER_8X8_INT,
)

from lib.retro.dither_error import (
    find_nearest_color,
    quantize_to_level,
    rgb_distance,
    lab_distance,
    floyd_steinberg_dither,
    atkinson_dither,
    sierra_dither,
    get_kernel,
    get_kernel_names,
    ERROR_DIFFUSION_KERNELS,
    FLOYD_STEINBERG,
    ATKINSON,
    SIERRA_LITE,
)

from lib.retro.dither_patterns import (
    list_patterns,
    get_pattern,
    tile_pattern,
    generate_diagonal_pattern,
    generate_dot_pattern,
    generate_circle_pattern,
    PATTERNS,
)


# =============================================================================
# Test Dither Types
# =============================================================================

class TestDitherTypes(unittest.TestCase):
    """Tests for dither_types module."""

    def test_dither_config_defaults(self):
        """Test default DitherConfig values."""
        config = DitherConfig()
        self.assertEqual(config.mode, "none")
        self.assertEqual(config.strength, 1.0)
        self.assertEqual(config.color_space, "rgb")
        self.assertTrue(config.serpentine)
        self.assertEqual(config.matrix_size, 4)
        self.assertIsNone(config.custom_pattern)
        self.assertEqual(config.levels, 2)

    def test_dither_config_validation(self):
        """Test DitherConfig validation."""
        # Valid config
        config = DitherConfig(mode="bayer_4x4", strength=0.5, levels=4)
        errors = config.validate()
        self.assertEqual(len(errors), 0)

        # Invalid mode
        config = DitherConfig(mode="invalid_mode")
        errors = config.validate()
        self.assertGreater(len(errors), 0)

        # Invalid strength
        config = DitherConfig(strength=2.0)
        errors = config.validate()
        self.assertGreater(len(errors), 0)

        # Invalid levels
        config = DitherConfig(levels=1)
        errors = config.validate()
        self.assertGreater(len(errors), 0)

    def test_dither_config_custom_pattern_validation(self):
        """Test custom pattern validation."""
        # Valid custom pattern
        pattern = [[0.0, 0.5], [1.0, 0.5]]
        config = DitherConfig(mode="custom", custom_pattern=pattern)
        errors = config.validate()
        self.assertEqual(len(errors), 0)

        # Custom mode without pattern
        config = DitherConfig(mode="custom")
        errors = config.validate()
        self.assertGreater(len(errors), 0)

        # Invalid pattern values
        pattern = [[0.0, 1.5], [1.0, 0.5]]
        config = DitherConfig(mode="custom", custom_pattern=pattern)
        errors = config.validate()
        self.assertGreater(len(errors), 0)

    def test_dither_config_serialization(self):
        """Test DitherConfig to_dict/from_dict."""
        config = DitherConfig(
            mode="atkinson",
            strength=0.8,
            levels=4,
            serpentine=False,
            color_space="lab"
        )
        data = config.to_dict()
        restored = DitherConfig.from_dict(data)
        self.assertEqual(restored.mode, "atkinson")
        self.assertEqual(restored.strength, 0.8)
        self.assertEqual(restored.levels, 4)
        self.assertFalse(restored.serpentine)
        self.assertEqual(restored.color_space, "lab")

    def test_dither_matrix_bayer_generation(self):
        """Test Bayer matrix generation."""
        # 2x2
        matrix = DitherMatrix.bayer(2)
        self.assertEqual(matrix.size, 2)
        self.assertEqual(len(matrix.matrix), 2)
        self.assertEqual(len(matrix.matrix[0]), 2)

        # 4x4
        matrix = DitherMatrix.bayer(4)
        self.assertEqual(matrix.size, 4)
        self.assertEqual(len(matrix.matrix), 4)

        # 8x8
        matrix = DitherMatrix.bayer(8)
        self.assertEqual(matrix.size, 8)
        self.assertEqual(len(matrix.matrix), 8)

    def test_dither_matrix_bayer_values(self):
        """Test Bayer matrix values are in correct range."""
        matrix = DitherMatrix.bayer(4)
        for row in matrix.matrix:
            for val in row:
                self.assertGreaterEqual(val, 0.0)
                self.assertLessEqual(val, 1.0)

    def test_dither_matrix_bayer_power_of_two(self):
        """Test Bayer matrix requires power of 2."""
        with self.assertRaises(ValueError):
            DitherMatrix.bayer(3)
        with self.assertRaises(ValueError):
            DitherMatrix.bayer(5)

    def test_dither_matrix_checkerboard(self):
        """Test checkerboard matrix."""
        matrix = DitherMatrix.checkerboard()
        self.assertEqual(matrix.size, 2)
        self.assertEqual(matrix.matrix, [[0.0, 1.0], [1.0, 0.0]])

    def test_dither_matrix_get_threshold(self):
        """Test threshold retrieval with wrapping."""
        matrix = DitherMatrix.bayer(4)

        # Same position should give same threshold
        self.assertEqual(matrix.get_threshold(0, 0), matrix.get_threshold(0, 0))
        self.assertEqual(matrix.get_threshold(4, 0), matrix.get_threshold(0, 0))
        self.assertEqual(matrix.get_threshold(0, 4), matrix.get_threshold(0, 0))
        self.assertEqual(matrix.get_threshold(4, 4), matrix.get_threshold(0, 0))

    def test_builtin_matrices(self):
        """Test built-in matrices dictionary."""
        self.assertIn("bayer_2x2", BUILTIN_MATRICES)
        self.assertIn("bayer_4x4", BUILTIN_MATRICES)
        self.assertIn("bayer_8x8", BUILTIN_MATRICES)
        self.assertIn("checkerboard", BUILTIN_MATRICES)

    def test_get_matrix(self):
        """Test get_matrix function."""
        matrix = get_matrix("bayer_4x4")
        self.assertIsNotNone(matrix)
        self.assertEqual(matrix.size, 4)

        matrix = get_matrix("nonexistent")
        self.assertIsNone(matrix)

    def test_list_matrices(self):
        """Test list_matrices function."""
        matrices = list_matrices()
        self.assertIn("bayer_4x4", matrices)
        self.assertIn("checkerboard", matrices)


# =============================================================================
# Test Ordered Dithering
# =============================================================================

class TestDitherOrdered(unittest.TestCase):
    """Tests for dither_ordered module."""

    def test_generate_bayer_matrix_2x2(self):
        """Test 2x2 Bayer matrix generation."""
        matrix = generate_bayer_matrix(2)
        self.assertEqual(matrix, BAYER_2X2_INT)

    def test_generate_bayer_matrix_4x4(self):
        """Test 4x4 Bayer matrix generation."""
        matrix = generate_bayer_matrix(4)
        self.assertEqual(matrix, BAYER_4X4_INT)

    def test_generate_bayer_matrix_8x8(self):
        """Test 8x8 Bayer matrix generation."""
        matrix = generate_bayer_matrix(8)
        self.assertEqual(matrix, BAYER_8X8_INT)

    def test_generate_bayer_matrix_16x16(self):
        """Test 16x16 Bayer matrix generation."""
        matrix = generate_bayer_matrix(16)
        self.assertEqual(len(matrix), 16)
        self.assertEqual(len(matrix[0]), 16)

        # Check values are in range 0 to 255
        for row in matrix:
            for val in row:
                self.assertGreaterEqual(val, 0)
                self.assertLessEqual(val, 255)

    def test_generate_bayer_matrix_invalid_size(self):
        """Test Bayer matrix with non-power-of-2 size."""
        with self.assertRaises(ValueError):
            generate_bayer_matrix(3)

    def test_normalize_matrix(self):
        """Test matrix normalization."""
        matrix = [[0, 2], [3, 1]]
        normalized = normalize_matrix(matrix)

        # Check normalized values
        self.assertAlmostEqual(normalized[0][0], 0.0, places=2)
        self.assertAlmostEqual(normalized[0][1], 2/3, places=2)
        self.assertAlmostEqual(normalized[1][0], 1.0, places=2)
        self.assertAlmostEqual(normalized[1][1], 1/3, places=2)

    def test_get_bayer_threshold(self):
        """Test threshold retrieval function."""
        # 2x2 matrix: [[0,2],[3,1]] normalized = [[0, 2/3], [1, 1/3]]
        threshold_00 = get_bayer_threshold(0, 0, 2)
        self.assertAlmostEqual(threshold_00, 0.0, places=2)

        threshold_10 = get_bayer_threshold(1, 0, 2)
        self.assertAlmostEqual(threshold_10, 2/3, places=2)

        # Test wrapping
        threshold_20 = get_bayer_threshold(2, 0, 2)
        self.assertAlmostEqual(threshold_20, threshold_00, places=2)


# =============================================================================
# Test Error Diffusion
# =============================================================================

class TestDitherError(unittest.TestCase):
    """Tests for dither_error module."""

    def test_rgb_distance(self):
        """Test RGB color distance."""
        # Same color
        self.assertEqual(rgb_distance((0, 0, 0), (0, 0, 0)), 0.0)
        self.assertEqual(rgb_distance((255, 255, 255), (255, 255, 255)), 0.0)

        # Different colors
        dist = rgb_distance((0, 0, 0), (255, 255, 255))
        self.assertAlmostEqual(dist, 441.67, places=1)

        # Partial difference
        dist = rgb_distance((100, 100, 100), (110, 100, 100))
        self.assertEqual(dist, 10.0)

    def test_lab_distance(self):
        """Test Lab color distance."""
        # Same color should be zero
        dist = lab_distance((128, 128, 128), (128, 128, 128))
        self.assertAlmostEqual(dist, 0.0, places=1)

    def test_quantize_to_level(self):
        """Test value quantization."""
        # 2 levels (0 and 255)
        self.assertEqual(quantize_to_level(0, 2), 0.0)
        self.assertEqual(quantize_to_level(127, 2), 0.0)
        self.assertEqual(quantize_to_level(128, 2), 255.0)

        # 4 levels
        self.assertEqual(quantize_to_level(0, 4), 0.0)
        self.assertEqual(quantize_to_level(64, 4), 85.0)
        self.assertEqual(quantize_to_level(170, 4), 170.0)

    def test_find_nearest_color_rgb(self):
        """Test finding nearest color in palette."""
        palette = [(0, 0, 0), (255, 255, 255), (255, 0, 0)]

        # Exact match
        result = find_nearest_color((255, 0, 0), palette)
        self.assertEqual(result, (255, 0, 0))

        # Close to black
        result = find_nearest_color((10, 10, 10), palette)
        self.assertEqual(result, (0, 0, 0))

        # Close to white
        result = find_nearest_color((250, 250, 250), palette)
        self.assertEqual(result, (255, 255, 255))

    def test_get_kernel(self):
        """Test kernel retrieval."""
        kernel = get_kernel("floyd_steinberg")
        self.assertIsNotNone(kernel)
        self.assertEqual(kernel["name"], "Floyd-Steinberg")

        kernel = get_kernel("atkinson")
        self.assertIsNotNone(kernel)
        self.assertIn("Atkinson", kernel["name"])

        kernel = get_kernel("nonexistent")
        self.assertIsNone(kernel)

    def test_get_kernel_names(self):
        """Test kernel name listing."""
        names = get_kernel_names()
        self.assertIn("floyd_steinberg", names)
        self.assertIn("atkinson", names)
        self.assertIn("sierra_lite", names)

    def test_error_diffusion_kernels(self):
        """Test kernel definitions."""
        # Floyd-Steinberg should have 4 neighbors
        self.assertEqual(len(FLOYD_STEINBERG["kernel"]), 4)

        # Atkinson should have 6 neighbors
        self.assertEqual(len(ATKINSON["kernel"]), 6)

        # Check weights sum roughly to 1
        fs_sum = sum(w for _, _, w in FLOYD_STEINBERG["kernel"])
        self.assertAlmostEqual(fs_sum, 1.0, places=2)


# =============================================================================
# Test Pattern Dithering
# =============================================================================

class TestDitherPatterns(unittest.TestCase):
    """Tests for dither_patterns module."""

    def test_list_patterns(self):
        """Test pattern listing."""
        patterns = list_patterns()
        self.assertIn("diagonal_lines", patterns)
        self.assertIn("horizontal_lines", patterns)
        self.assertIn("crosshatch", patterns)

    def test_get_pattern(self):
        """Test pattern retrieval."""
        pattern = get_pattern("diagonal_lines")
        self.assertIsNotNone(pattern)
        self.assertEqual(len(pattern), 2)

        pattern = get_pattern("nonexistent")
        self.assertIsNone(pattern)

    def test_tile_pattern(self):
        """Test pattern tiling."""
        pattern = [[0.0, 1.0], [1.0, 0.0]]
        tiled = tile_pattern(pattern, 4, 4)

        self.assertEqual(len(tiled), 4)
        self.assertEqual(len(tiled[0]), 4)

        # Check pattern repeats correctly
        self.assertEqual(tiled[0][0], tiled[2][0])
        self.assertEqual(tiled[0][2], tiled[0][0])

    def test_generate_diagonal_pattern(self):
        """Test diagonal pattern generation."""
        pattern = generate_diagonal_pattern(spacing=2, angle=45)
        self.assertIsNotNone(pattern)

        # Should be 4x4 for spacing=2
        self.assertEqual(len(pattern), 4)

    def test_generate_dot_pattern(self):
        """Test dot pattern generation."""
        pattern = generate_dot_pattern(dot_size=2, spacing=2)
        self.assertIsNotNone(pattern)

        # Size should be dot_size + spacing
        self.assertEqual(len(pattern), 4)

    def test_generate_circle_pattern(self):
        """Test circle pattern generation."""
        pattern = generate_circle_pattern(radius=2)
        self.assertIsNotNone(pattern)

        # Size should be 2*radius + 2
        self.assertEqual(len(pattern), 6)

    def test_builtin_patterns(self):
        """Test built-in patterns exist."""
        self.assertIn("diagonal_lines", PATTERNS)
        self.assertIn("horizontal_lines", PATTERNS)
        self.assertIn("vertical_lines", PATTERNS)
        self.assertIn("crosshatch", PATTERNS)
        self.assertIn("diamond", PATTERNS)


# =============================================================================
# Test Main Dither Module
# =============================================================================

@unittest.skipUnless(HAS_PIL, "PIL/Pillow required for integration tests")
class TestDitherModule(unittest.TestCase):
    """Tests for main dither module."""

    def setUp(self):
        """Create test images."""
        # Create simple gradient image
        self.gradient = Image.new("L", (100, 100))
        for x in range(100):
            for y in range(100):
                self.gradient.putpixel((x, y), x)

        # Create solid color image
        self.solid = Image.new("RGB", (50, 50), (128, 128, 128))

    def test_dither_none_mode(self):
        """Test no dithering mode."""
        from lib.retro.dither import dither

        config = DitherConfig(mode="none")
        result = dither(self.solid, config)

        self.assertIsInstance(result, Image.Image)
        self.assertEqual(result.size, self.solid.size)

    def test_dither_bayer_4x4(self):
        """Test Bayer 4x4 dithering."""
        from lib.retro.dither import dither

        config = DitherConfig(mode="bayer_4x4", levels=4)
        result = dither(self.gradient, config)

        self.assertIsInstance(result, Image.Image)
        self.assertEqual(result.size, self.gradient.size)

    def test_dither_floyd_steinberg(self):
        """Test Floyd-Steinberg dithering."""
        from lib.retro.dither import dither

        config = DitherConfig(mode="floyd_steinberg", levels=2)
        result = dither(self.gradient, config)

        self.assertIsInstance(result, Image.Image)
        self.assertEqual(result.size, self.gradient.size)

    def test_dither_atkinson(self):
        """Test Atkinson dithering."""
        from lib.retro.dither import dither

        config = DitherConfig(mode="atkinson", levels=2)
        result = dither(self.gradient, config)

        self.assertIsInstance(result, Image.Image)
        self.assertEqual(result.size, self.gradient.size)

    def test_dither_with_palette(self):
        """Test dithering with custom palette."""
        from lib.retro.dither import dither

        palette = [(0, 0, 0), (255, 255, 255)]
        config = DitherConfig(mode="floyd_steinberg", levels=2)
        result = dither(self.gradient.convert("RGB"), config, palette=palette)

        self.assertIsInstance(result, Image.Image)

    def test_dither_custom_pattern(self):
        """Test custom pattern dithering."""
        from lib.retro.dither import dither

        custom_pattern = [[0.0, 0.5], [1.0, 0.5]]
        config = DitherConfig(
            mode="custom",
            custom_pattern=custom_pattern,
            levels=2
        )
        result = dither(self.gradient, config)

        self.assertIsInstance(result, Image.Image)

    def test_dither_invalid_config(self):
        """Test dithering with invalid config."""
        from lib.retro.dither import dither

        config = DitherConfig(mode="invalid", strength=2.0)

        with self.assertRaises(ValueError):
            dither(self.solid, config)

    def test_dither_strength(self):
        """Test dithering strength adjustment."""
        from lib.retro.dither import dither

        # Full strength
        config_full = DitherConfig(mode="bayer_4x4", strength=1.0, levels=2)
        result_full = dither(self.gradient, config_full)

        # Half strength
        config_half = DitherConfig(mode="bayer_4x4", strength=0.5, levels=2)
        result_half = dither(self.gradient, config_half)

        # Results should be different
        # (though we can't easily test the visual difference)
        self.assertIsInstance(result_full, Image.Image)
        self.assertIsInstance(result_half, Image.Image)

    def test_dither_1bit_convenience(self):
        """Test dither_1bit convenience function."""
        from lib.retro.dither import dither_1bit

        result = dither_1bit(self.gradient, mode="atkinson")

        self.assertIsInstance(result, Image.Image)
        self.assertEqual(result.mode, "1")


# =============================================================================
# Test Utility Functions
# =============================================================================

class TestDitherUtils(unittest.TestCase):
    """Tests for utility functions."""

    def test_get_available_modes(self):
        """Test mode listing."""
        from lib.retro.dither import get_available_modes

        modes = get_available_modes()

        self.assertIn("ordered", modes)
        self.assertIn("error_diffusion", modes)
        self.assertIn("pattern", modes)

        self.assertIn("bayer_4x4", modes["ordered"])
        self.assertIn("floyd_steinberg", modes["error_diffusion"])

    def test_list_all_modes(self):
        """Test flat mode listing."""
        from lib.retro.dither import list_all_modes

        modes = list_all_modes()

        self.assertIn("bayer_4x4", modes)
        self.assertIn("floyd_steinberg", modes)
        self.assertIn("atkinson", modes)

    def test_is_valid_mode(self):
        """Test mode validation."""
        from lib.retro.dither import is_valid_mode

        self.assertTrue(is_valid_mode("bayer_4x4"))
        self.assertTrue(is_valid_mode("floyd_steinberg"))
        self.assertTrue(is_valid_mode("atkinson"))
        self.assertFalse(is_valid_mode("invalid_mode"))

    def test_get_mode_description(self):
        """Test mode descriptions."""
        from lib.retro.dither import get_mode_description

        desc = get_mode_description("bayer_4x4")
        self.assertIsInstance(desc, str)
        self.assertGreater(len(desc), 0)

        desc = get_mode_description("atkinson")
        self.assertIn("Macintosh", desc)

    def test_info(self):
        """Test module info."""
        from lib.retro.dither import info

        info_dict = info()

        self.assertIn("modes_available", info_dict)
        self.assertIn("patterns_available", info_dict)
        self.assertGreater(info_dict["modes_available"], 0)


# =============================================================================
# Run Tests
# =============================================================================

if __name__ == "__main__":
    unittest.main(verbosity=2)

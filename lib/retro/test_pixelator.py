"""
Tests for pixelator module.

Run with: pytest lib/retro/test_pixelator.py -v
"""

import pytest
import os
import tempfile
from pathlib import Path

# Check for optional dependencies
try:
    from PIL import Image
    import numpy as np
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

from lib.retro.pixel_types import PixelStyle, PixelationConfig, ColorPalette
from lib.retro.pixelator import (
    pixelate,
    downscale_image,
    pixelate_block,
    enhance_edges,
    posterize,
    quantize_colors,
    quantize_to_palette,
    extract_palette,
    pixelate_32bit,
    pixelate_16bit,
    pixelate_8bit,
    pixelate_4bit,
    pixelate_2bit,
    pixelate_1bit,
)


@pytest.fixture
def sample_image():
    """Create a sample test image."""
    if not HAS_DEPS:
        pytest.skip("PIL and numpy required")
    # Create a 100x100 RGB image with gradient
    img = Image.new("RGB", (100, 100))
    pixels = img.load()
    for y in range(100):
        for x in range(100):
            pixels[x, y] = (x * 2, y * 2, 128)
    return img


@pytest.fixture
def simple_image():
    """Create a simple test image with few colors."""
    if not HAS_DEPS:
        pytest.skip("PIL and numpy required")
    # Create a 50x50 image with just a few colors
    img = Image.new("RGB", (50, 50))
    pixels = img.load()
    for y in range(50):
        for x in range(50):
            if x < 25 and y < 25:
                pixels[x, y] = (255, 0, 0)  # Red quadrant
            elif x >= 25 and y < 25:
                pixels[x, y] = (0, 255, 0)  # Green quadrant
            elif x < 25 and y >= 25:
                pixels[x, y] = (0, 0, 255)  # Blue quadrant
            else:
                pixels[x, y] = (255, 255, 255)  # White quadrant
    return img


class TestPixelate:
    """Tests for main pixelate function."""

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL and numpy required")
    def test_pixelate_basic(self, sample_image):
        """Test basic pixelation."""
        config = PixelationConfig()
        result = pixelate(sample_image, config)

        assert result.image is not None
        assert result.original_resolution == (100, 100)
        assert result.processing_time > 0

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL and numpy required")
    def test_pixelate_with_target_resolution(self, sample_image):
        """Test pixelation with target resolution."""
        config = PixelationConfig(target_resolution=(50, 50))
        result = pixelate(sample_image, config)

        assert result.pixel_resolution == (50, 50)

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL and numpy required")
    def test_pixelate_with_pixel_size(self, sample_image):
        """Test pixelation with pixel size."""
        config = PixelationConfig(style=PixelStyle(pixel_size=4))
        result = pixelate(sample_image, config)

        assert result.image is not None

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL and numpy required")
    def test_pixelate_with_output_scale(self, sample_image):
        """Test pixelation with output scale."""
        config = PixelationConfig(
            target_resolution=(25, 25),
            output_scale=2
        )
        result = pixelate(sample_image, config)

        assert result.output_resolution == (50, 50)

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL and numpy required")
    def test_pixelate_preserves_aspect_ratio(self, sample_image):
        """Test that aspect ratio is preserved by default."""
        config = PixelationConfig(target_resolution=(50, 100))
        result = pixelate(sample_image, config)

        # 100x100 source into 50x100 target should fit to 50x50
        assert result.pixel_resolution == (50, 50)

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL and numpy required")
    def test_pixelate_invalid_config(self, sample_image):
        """Test pixelation with invalid config returns warnings."""
        config = PixelationConfig(style=PixelStyle(pixel_size=-1))
        result = pixelate(sample_image, config)

        assert len(result.warnings) > 0
        assert result.image is None


class TestDownscaleImage:
    """Tests for downscale_image function."""

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL required")
    def test_downscale_basic(self, sample_image):
        """Test basic downscaling."""
        result = downscale_image(sample_image, (50, 50))
        assert result.size == (50, 50)

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL required")
    def test_downscale_nearest(self, sample_image):
        """Test downscaling with nearest filter."""
        result = downscale_image(sample_image, (50, 50), "nearest")
        assert result.size == (50, 50)

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL required")
    def test_downscale_bilinear(self, sample_image):
        """Test downscaling with bilinear filter."""
        result = downscale_image(sample_image, (50, 50), "bilinear")
        assert result.size == (50, 50)


class TestPixelateBlock:
    """Tests for pixelate_block function."""

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL required")
    def test_pixelate_block_2x2(self, sample_image):
        """Test 2x2 block pixelation."""
        result = pixelate_block(sample_image, 2)
        assert result.size == (100, 100)  # Size unchanged

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL required")
    def test_pixelate_block_4x4(self, sample_image):
        """Test 4x4 block pixelation."""
        result = pixelate_block(sample_image, 4)
        assert result.size == (100, 100)

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL required")
    def test_pixelate_block_1(self, sample_image):
        """Test block size 1 returns original."""
        result = pixelate_block(sample_image, 1)
        assert result.size == (100, 100)


class TestEnhanceEdges:
    """Tests for enhance_edges function."""

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL required")
    def test_enhance_edges_zero_strength(self, sample_image):
        """Test zero strength returns original."""
        result = enhance_edges(sample_image, threshold=0.1, strength=0.0)
        assert result.size == sample_image.size

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL required")
    def test_enhance_edges_with_strength(self, sample_image):
        """Test edge enhancement with strength."""
        result = enhance_edges(sample_image, threshold=0.1, strength=0.5)
        assert result.size == sample_image.size


class TestPosterize:
    """Tests for posterize function."""

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL required")
    def test_posterize_4_levels(self, sample_image):
        """Test posterization with 4 levels."""
        result = posterize(sample_image, 4)
        assert result.size == sample_image.size

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL required")
    def test_posterize_2_levels(self, sample_image):
        """Test posterization with 2 levels."""
        result = posterize(sample_image, 2)
        assert result.size == sample_image.size


class TestQuantizeColors:
    """Tests for quantize_colors function."""

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL required")
    def test_quantize_16_colors(self, sample_image):
        """Test quantization to 16 colors."""
        result = quantize_colors(sample_image, 16)
        assert result.mode == "P"  # Palette mode

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL required")
    def test_quantize_4_colors(self, sample_image):
        """Test quantization to 4 colors."""
        result = quantize_colors(sample_image, 4)
        assert result.mode == "P"


class TestQuantizeToPalette:
    """Tests for quantize_to_palette function."""

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL required")
    def test_quantize_to_custom_palette(self, simple_image):
        """Test quantization to custom palette."""
        palette = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 255)]
        result = quantize_to_palette(simple_image, palette)
        assert result.size == simple_image.size
        assert result.mode == "RGB"

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL required")
    def test_quantize_empty_palette(self, sample_image):
        """Test with empty palette returns original."""
        result = quantize_to_palette(sample_image, [])
        assert result.size == sample_image.size


class TestExtractPalette:
    """Tests for extract_palette function."""

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL required")
    def test_extract_4_colors(self, simple_image):
        """Test extracting 4 colors."""
        colors = extract_palette(simple_image, 4)
        assert len(colors) == 4

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL required")
    def test_extract_16_colors(self, sample_image):
        """Test extracting 16 colors."""
        colors = extract_palette(sample_image, 16)
        assert len(colors) == 16


class TestModeFunctions:
    """Tests for mode-specific pixelation functions."""

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL required")
    def test_pixelate_32bit(self, sample_image):
        """Test 32-bit mode."""
        style = PixelStyle(mode="32bit")
        result = pixelate_32bit(sample_image, style)
        assert result is not None

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL required")
    def test_pixelate_16bit(self, sample_image):
        """Test 16-bit mode."""
        style = PixelStyle(mode="16bit", color_limit=256)
        result = pixelate_16bit(sample_image, style)
        assert result is not None

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL required")
    def test_pixelate_8bit(self, sample_image):
        """Test 8-bit mode."""
        style = PixelStyle(mode="8bit", color_limit=64)
        result = pixelate_8bit(sample_image, style)
        assert result is not None

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL required")
    def test_pixelate_4bit(self, sample_image):
        """Test 4-bit mode."""
        style = PixelStyle(mode="4bit", color_limit=16)
        result = pixelate_4bit(sample_image, style)
        assert result is not None

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL required")
    def test_pixelate_2bit(self, sample_image):
        """Test 2-bit mode."""
        style = PixelStyle(mode="2bit", color_limit=4)
        result = pixelate_2bit(sample_image, style)
        assert result is not None

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL required")
    def test_pixelate_1bit(self, sample_image):
        """Test 1-bit mode."""
        style = PixelStyle(mode="1bit", color_limit=2)
        result = pixelate_1bit(sample_image, style)
        assert result is not None
        assert result.mode == "1"

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL required")
    def test_pixelate_1bit_dithered(self, sample_image):
        """Test 1-bit mode with dithering."""
        style = PixelStyle(mode="1bit", color_limit=2, dither_mode="ordered")
        result = pixelate_1bit(sample_image, style)
        assert result is not None
        assert result.mode == "1"


class TestConsolePresets:
    """Tests for console preset configurations."""

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL required")
    def test_snes_preset(self, sample_image):
        """Test SNES preset produces correct output."""
        config = PixelationConfig.for_console("snes")
        result = pixelate(sample_image, config)
        assert result.image is not None
        # SNES preset targets 256x224, 100x100 source fits to 224x224 preserving aspect

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL required")
    def test_nes_preset(self, sample_image):
        """Test NES preset produces correct output."""
        config = PixelationConfig.for_console("nes")
        result = pixelate(sample_image, config)
        assert result.image is not None

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL required")
    def test_gameboy_preset(self, sample_image):
        """Test Game Boy preset produces correct output."""
        config = PixelationConfig.for_console("gameboy")
        result = pixelate(sample_image, config)
        assert result.image is not None

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL required")
    def test_pico8_preset(self, sample_image):
        """Test PICO-8 preset produces correct output."""
        config = PixelationConfig.for_console("pico8")
        result = pixelate(sample_image, config)
        assert result.image is not None


class TestInputFormats:
    """Tests for different input formats."""

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL and numpy required")
    def test_numpy_array_input(self):
        """Test numpy array input."""
        arr = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)
        config = PixelationConfig()
        result = pixelate(arr, config)
        assert result.image is not None

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL and numpy required")
    def test_file_path_input(self):
        """Test file path input."""
        # Create temporary image file
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
            temp_path = f.name
            img = Image.new("RGB", (50, 50), color=(128, 128, 128))
            img.save(temp_path)

        try:
            config = PixelationConfig()
            result = pixelate(temp_path, config)
            assert result.image is not None
        finally:
            os.unlink(temp_path)

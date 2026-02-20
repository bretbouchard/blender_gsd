"""
Tests for quantizer module.

Run with: pytest lib/retro/test_quantizer.py -v
"""

import pytest

# Check for optional dependencies
try:
    from PIL import Image
    import numpy as np
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False

from lib.retro.quantizer import (
    quantize_colors,
    quantize_to_palette,
    extract_palette,
    median_cut_quantize,
    kmeans_quantize,
    octree_quantize,
    nearest_color_match,
    build_weighted_palette,
    count_colors,
    get_color_histogram,
    OctreeNode,
)


@pytest.fixture
def gradient_image():
    """Create a gradient test image."""
    if not HAS_DEPS:
        pytest.skip("PIL and numpy required")
    img = Image.new("RGB", (100, 100))
    pixels = img.load()
    for y in range(100):
        for x in range(100):
            pixels[x, y] = (x * 2, y * 2, 128)
    return img


@pytest.fixture
def few_colors_image():
    """Create an image with few colors."""
    if not HAS_DEPS:
        pytest.skip("PIL and numpy required")
    img = Image.new("RGB", (50, 50))
    pixels = img.load()
    for y in range(50):
        for x in range(50):
            if x < 25 and y < 25:
                pixels[x, y] = (255, 0, 0)
            elif x >= 25 and y < 25:
                pixels[x, y] = (0, 255, 0)
            elif x < 25 and y >= 25:
                pixels[x, y] = (0, 0, 255)
            else:
                pixels[x, y] = (255, 255, 255)
    return img


class TestQuantizeColors:
    """Tests for quantize_colors function."""

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL and numpy required")
    def test_quantize_median_cut(self, gradient_image):
        """Test median cut quantization."""
        result = quantize_colors(gradient_image, 16, method="median_cut")
        assert result is not None
        assert result.size == gradient_image.size

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL and numpy required")
    def test_quantize_kmeans(self, gradient_image):
        """Test k-means quantization."""
        result = quantize_colors(gradient_image, 16, method="kmeans")
        assert result is not None
        assert result.size == gradient_image.size

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL and numpy required")
    def test_quantize_octree(self, gradient_image):
        """Test octree quantization."""
        result = quantize_colors(gradient_image, 16, method="octree")
        assert result is not None
        assert result.size == gradient_image.size

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL and numpy required")
    def test_quantize_reduces_colors(self, gradient_image):
        """Test that quantization reduces color count."""
        original_count = count_colors(gradient_image)
        result = quantize_colors(gradient_image, 8, method="median_cut")
        new_count = count_colors(result)
        assert new_count <= 8
        assert new_count < original_count


class TestQuantizeToPalette:
    """Tests for quantize_to_palette function."""

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL and numpy required")
    def test_quantize_to_custom_palette(self, few_colors_image):
        """Test quantization to custom palette."""
        palette = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 255)]
        result = quantize_to_palette(few_colors_image, palette)
        assert result is not None
        assert result.size == few_colors_image.size

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL and numpy required")
    def test_quantize_empty_palette(self, gradient_image):
        """Test with empty palette returns original."""
        result = quantize_to_palette(gradient_image, [])
        assert result.size == gradient_image.size

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL and numpy required")
    def test_quantize_single_color_palette(self, gradient_image):
        """Test with single color palette."""
        palette = [(128, 128, 128)]
        result = quantize_to_palette(gradient_image, palette)
        assert result is not None
        # All pixels should be the single palette color
        pixels = list(result.getdata())
        assert all(p == (128, 128, 128) for p in pixels)


class TestExtractPalette:
    """Tests for extract_palette function."""

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL and numpy required")
    def test_extract_few_colors(self, few_colors_image):
        """Test extracting colors from simple image."""
        colors = extract_palette(few_colors_image, 4)
        assert len(colors) == 4

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL and numpy required")
    def test_extract_with_method(self, gradient_image):
        """Test extraction with different methods."""
        colors_median = extract_palette(gradient_image, 8, method="median_cut")
        colors_kmeans = extract_palette(gradient_image, 8, method="kmeans")

        assert len(colors_median) == 8
        assert len(colors_kmeans) == 8


class TestMedianCutQuantize:
    """Tests for median_cut_quantize function."""

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL and numpy required")
    def test_basic(self, gradient_image):
        """Test basic median cut."""
        result = median_cut_quantize(gradient_image, 16)
        assert result is not None
        assert result.size == gradient_image.size

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL and numpy required")
    def test_small_color_count(self, few_colors_image):
        """Test with small color count."""
        result = median_cut_quantize(few_colors_image, 4)
        assert result is not None


class TestKMeansQuantize:
    """Tests for kmeans_quantize function."""

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL and numpy required")
    def test_basic(self, gradient_image):
        """Test basic k-means."""
        result = kmeans_quantize(gradient_image, 16)
        assert result is not None
        assert result.size == gradient_image.size

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL and numpy required")
    def test_iterations(self, gradient_image):
        """Test with different iteration counts."""
        result_few = kmeans_quantize(gradient_image, 8, max_iterations=5)
        result_more = kmeans_quantize(gradient_image, 8, max_iterations=20)
        assert result_few is not None
        assert result_more is not None


class TestOctreeQuantize:
    """Tests for octree_quantize function."""

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL required")
    def test_basic(self, gradient_image):
        """Test basic octree."""
        result = octree_quantize(gradient_image, 16)
        assert result is not None
        assert result.size == gradient_image.size


class TestOctreeNode:
    """Tests for OctreeNode class."""

    def test_init(self):
        """Test node initialization."""
        node = OctreeNode(0)
        assert node.level == 0
        assert node.pixel_count == 0
        assert node.parent is None

    def test_get_child_index(self):
        """Test child index calculation."""
        node = OctreeNode(0)
        # Test all combinations at level 0
        assert node.get_child_index(0, 0, 0) == 0
        assert node.get_child_index(128, 0, 0) == 1
        assert node.get_child_index(0, 128, 0) == 2
        assert node.get_child_index(128, 128, 0) == 3
        assert node.get_child_index(0, 0, 128) == 4
        assert node.get_child_index(128, 0, 128) == 5
        assert node.get_child_index(0, 128, 128) == 6
        assert node.get_child_index(128, 128, 128) == 7

    def test_add_color(self):
        """Test adding colors."""
        node = OctreeNode(7)  # Leaf level
        node.add_color(255, 128, 64)
        node.add_color(255, 128, 64)

        assert node.pixel_count == 2
        assert node.red_sum == 510
        assert node.green_sum == 256
        assert node.blue_sum == 128

    def test_get_color(self):
        """Test getting average color."""
        node = OctreeNode(7)  # Leaf level
        node.add_color(255, 0, 0)
        node.add_color(0, 255, 0)

        color = node.get_color()
        assert color == (127, 127, 0)


class TestNearestColorMatch:
    """Tests for nearest_color_match function."""

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL and numpy required")
    def test_basic(self, gradient_image):
        """Test basic color matching."""
        palette = [(0, 0, 0), (255, 255, 255), (128, 128, 128)]
        result = nearest_color_match(gradient_image, palette)
        assert result is not None
        assert result.size == gradient_image.size


class TestBuildWeightedPalette:
    """Tests for build_weighted_palette function."""

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL and numpy required")
    def test_basic(self, gradient_image):
        """Test building weighted palette."""
        palette = build_weighted_palette(gradient_image, 8)
        assert len(palette) == 8

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL and numpy required")
    def test_with_weights(self, gradient_image):
        """Test with custom weights."""
        palette = build_weighted_palette(
            gradient_image, 8,
            saturation_weight=0.5,
            brightness_weight=0.5
        )
        assert len(palette) == 8


class TestCountColors:
    """Tests for count_colors function."""

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL and numpy required")
    def test_few_colors(self, few_colors_image):
        """Test counting colors in simple image."""
        count = count_colors(few_colors_image)
        assert count == 4

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL and numpy required")
    def test_gradient_colors(self, gradient_image):
        """Test counting colors in gradient."""
        count = count_colors(gradient_image)
        assert count > 100  # Many unique colors


class TestGetColorHistogram:
    """Tests for get_color_histogram function."""

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL and numpy required")
    def test_few_colors(self, few_colors_image):
        """Test histogram of simple image."""
        hist = get_color_histogram(few_colors_image)
        assert len(hist) == 4
        # Each color should have 625 pixels (25*25)
        for count in hist.values():
            assert count == 625

    @pytest.mark.skipif(not HAS_DEPS, reason="PIL and numpy required")
    def test_empty_max_colors(self, gradient_image):
        """Test with limited max_colors."""
        hist = get_color_histogram(gradient_image, max_colors=10)
        # Should return empty dict when colors exceed max
        assert hist == {}

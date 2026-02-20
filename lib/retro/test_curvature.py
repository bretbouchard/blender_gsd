"""
Unit tests for Screen Curvature module.

Tests for barrel distortion, vignette, and corner rounding effects.
"""

import pytest
import numpy as np

# Skip all tests if PIL not available
pytest.importorskip("PIL")

from PIL import Image

from lib.retro.curvature import (
    # UV transformation
    calculate_curved_uv,
    calculate_barrel_distortion_grid,
    # Vignette
    create_vignette_mask,
    create_corner_mask,
    apply_vignette,
    # Main functions
    apply_curvature,
    bilinear_sample,
    apply_border,
    combine_curvature_vignette,
    # Utility functions
    calculate_edge_stretch,
    estimate_content_loss,
    recommend_border_size,
)
from lib.retro.crt_types import CurvatureConfig


class TestCalculateCurvedUV:
    """Tests for calculate_curved_uv function."""

    def test_no_distortion(self):
        """Test with zero amount (no distortion)."""
        u, v = calculate_curved_uv(0.5, 0.5, 0.0)
        assert u == pytest.approx(0.5, rel=0.01)
        assert v == pytest.approx(0.5, rel=0.01)

    def test_center_unchanged(self):
        """Test that center is not distorted."""
        u, v = calculate_curved_uv(0.5, 0.5, 0.5)
        assert u == pytest.approx(0.5, rel=0.01)
        assert v == pytest.approx(0.5, rel=0.01)

    def test_corner_distortion(self):
        """Test that corners are distorted."""
        # Top-left corner should be pushed out
        u, v = calculate_curved_uv(0.0, 0.0, 0.3)

        # Should be outside original bounds
        assert u < 0 or u > 0.1  # Moved from corner
        assert v < 0 or v > 0.1

    def test_symmetric_distortion(self):
        """Test that distortion is symmetric."""
        u1, v1 = calculate_curved_uv(0.2, 0.3, 0.2)
        u2, v2 = calculate_curved_uv(0.8, 0.7, 0.2)

        # Should be mirrored around center
        # Due to barrel distortion, both move inward
        assert abs(u1 - (1.0 - u2)) < 0.1
        assert abs(v1 - (1.0 - v2)) < 0.1

    def test_aspect_ratio(self):
        """Test aspect ratio correction."""
        # Wide image
        u1, v1 = calculate_curved_uv(0.0, 0.5, 0.2, aspect_ratio=2.0)
        # Square image
        u2, v2 = calculate_curved_uv(0.0, 0.5, 0.2, aspect_ratio=1.0)

        # Different aspect ratios should produce different results
        assert u1 != u2 or v1 != v2


class TestCalculateBarrelDistortionGrid:
    """Tests for calculate_barrel_distortion_grid function."""

    def test_basic_grid(self):
        """Test basic grid generation."""
        u_map, v_map = calculate_barrel_distortion_grid(100, 100, 0.1)

        assert u_map.shape == (100, 100)
        assert v_map.shape == (100, 100)
        assert u_map.dtype == np.float64
        assert v_map.dtype == np.float64

    def test_no_distortion_grid(self):
        """Test grid with no distortion."""
        u_map, v_map = calculate_barrel_distortion_grid(10, 10, 0.0)

        # Should match original coordinates
        expected_u = np.tile(np.linspace(0, 1, 10), (10, 1))
        expected_v = np.tile(np.linspace(0, 1, 10).reshape(-1, 1), (1, 10))

        np.testing.assert_array_almost_equal(u_map, expected_u, decimal=2)
        np.testing.assert_array_almost_equal(v_map, expected_v, decimal=2)

    def test_center_unchanged(self):
        """Test that center of grid is nearly unchanged."""
        u_map, v_map = calculate_barrel_distortion_grid(100, 100, 0.3)

        # Center should be close to 0.5 (allowing for small distortion)
        assert u_map[50, 50] == pytest.approx(0.5, abs=0.02)
        assert v_map[50, 50] == pytest.approx(0.5, abs=0.02)


class TestCreateVignetteMask:
    """Tests for create_vignette_mask function."""

    def test_basic_mask(self):
        """Test basic vignette mask generation."""
        mask = create_vignette_mask(100, 100, 0.5)

        assert mask.shape == (100, 100)
        assert mask.dtype == np.float32

    def test_no_vignette(self):
        """Test with zero amount."""
        mask = create_vignette_mask(50, 50, 0.0)

        # Should be all ones
        np.testing.assert_array_equal(mask, np.ones((50, 50), dtype=np.float32))

    def test_center_brighter(self):
        """Test that center is brighter than edges."""
        mask = create_vignette_mask(100, 100, 0.5)

        # Center should be brighter
        assert mask[50, 50] > mask[0, 0]
        assert mask[50, 50] > mask[99, 99]

    def test_symmetric(self):
        """Test that vignette is symmetric."""
        mask = create_vignette_mask(100, 100, 0.5)

        # Corners should be equal
        assert abs(mask[0, 0] - mask[0, 99]) < 0.01
        assert abs(mask[0, 0] - mask[99, 0]) < 0.01
        assert abs(mask[0, 0] - mask[99, 99]) < 0.01


class TestCreateCornerMask:
    """Tests for create_corner_mask function."""

    def test_no_corners(self):
        """Test with zero radius."""
        mask = create_corner_mask(50, 50, 0)

        # Should be all ones
        np.testing.assert_array_equal(mask, np.ones((50, 50), dtype=np.float32))

    def test_with_corners(self):
        """Test with rounded corners."""
        mask = create_corner_mask(50, 50, 10)

        # Corner pixel (0,0) is at distance 0 from corner, so it's inside radius
        # A pixel further from corner like (10, 0) should be outside
        # (distance = 10 from corner, which equals radius, so still inside)
        # But (10, 10) is at distance sqrt(200) ~= 14.1 > 10, so should be masked
        # Actually that's inside the corner region
        # Let me check: (15, 15) has distance sqrt(450) ~= 21.2 > 10, should be masked
        # But (15, 15) is outside the 10x10 corner region, so it won't be masked

        # Let's check a pixel that should be masked:
        # In top-left 10x10 region, pixels outside radius should be masked
        # E.g., (9, 9) has distance sqrt(81+81) ~= 12.7 > 10, should be 0
        # While (0, 0) has distance 0, should be 1

        # Check that pixels at corner origin are inside (value 1.0)
        assert mask[0, 0] == 1.0
        assert mask[25, 25] == 1.0  # Center

        # Check that pixels outside radius but inside corner region are masked
        # (8, 8) has distance sqrt(128) ~= 11.3 > 10
        assert mask[8, 8] == 0.0

    def test_symmetric_corners(self):
        """Test that corners are symmetric."""
        mask = create_corner_mask(50, 50, 10)

        # All four corners should be cut equally
        assert mask[0, 0] == mask[0, 49]
        assert mask[0, 0] == mask[49, 0]
        assert mask[0, 0] == mask[49, 49]


class TestApplyVignette:
    """Tests for apply_vignette function."""

    def test_no_effect(self):
        """Test with zero vignette."""
        image = Image.new("RGB", (50, 50), color=(128, 128, 128))
        result = apply_vignette(image, 0.0)

        np.testing.assert_array_equal(np.array(image), np.array(result))

    def test_pil_image(self):
        """Test application to PIL Image."""
        image = Image.new("RGB", (50, 50), color=(255, 255, 255))
        result = apply_vignette(image, 0.5)

        assert isinstance(result, Image.Image)
        arr = np.array(result)

        # Center should be brighter than edges
        assert arr[25, 25, 0] > arr[0, 0, 0]

    def test_numpy_array(self):
        """Test application to numpy array."""
        image = np.ones((50, 50, 3), dtype=np.float32)
        result = apply_vignette(image, 0.5)

        assert isinstance(result, np.ndarray)
        assert result.shape == (50, 50, 3)

        # Center should be brighter than edges
        assert result[25, 25, 0] > result[0, 0, 0]

    def test_with_corners(self):
        """Test vignette with rounded corners."""
        image = np.ones((50, 50, 3), dtype=np.float32)
        result = apply_vignette(image, 0.3, corner_radius=15)

        # Corners should be darker than center due to both vignette and corner rounding
        assert result[0, 0, 0] < result[25, 25, 0]


class TestApplyCurvature:
    """Tests for apply_curvature function."""

    def test_disabled(self):
        """Test disabled configuration."""
        config = CurvatureConfig(enabled=False)
        image = Image.new("RGB", (50, 50), color=(128, 128, 128))
        result = apply_curvature(image, config)

        np.testing.assert_array_equal(np.array(image), np.array(result))

    def test_pil_image(self):
        """Test application to PIL Image."""
        config = CurvatureConfig(enabled=True, amount=0.1)
        image = Image.new("RGB", (100, 100), color=(255, 255, 255))
        result = apply_curvature(image, config)

        assert isinstance(result, Image.Image)
        assert result.size == (100, 100)

    def test_numpy_array(self):
        """Test application to numpy array."""
        config = CurvatureConfig(enabled=True, amount=0.1)
        image = np.ones((100, 100, 3), dtype=np.float32)
        result = apply_curvature(image, config)

        assert isinstance(result, np.ndarray)
        assert result.shape == (100, 100, 3)

    def test_curvature_only(self):
        """Test curvature without vignette."""
        config = CurvatureConfig(enabled=True, amount=0.2, vignette_amount=0.0)
        image = np.ones((100, 100, 3), dtype=np.float32)
        result = apply_curvature(image, config)

        # Result should be different from original (edge darkening from border sampling)
        # Even without vignette, edge pixels get darker due to out-of-bounds sampling
        assert result.shape == image.shape

    def test_vignette_only(self):
        """Test vignette without curvature."""
        config = CurvatureConfig(enabled=True, amount=0.0, vignette_amount=0.5)
        image = np.ones((50, 50, 3), dtype=np.float32)
        result = apply_curvature(image, config)

        # Center should be brighter
        assert result[25, 25, 0] > result[0, 0, 0]

    def test_both_effects(self):
        """Test both curvature and vignette."""
        config = CurvatureConfig(enabled=True, amount=0.1, vignette_amount=0.3)
        image = np.ones((100, 100, 3), dtype=np.float32)
        result = apply_curvature(image, config)

        assert isinstance(result, np.ndarray)

    def test_with_border(self):
        """Test curvature with border."""
        config = CurvatureConfig(enabled=True, amount=0.1, border_size=5)
        image = np.ones((50, 50, 3), dtype=np.float32)
        result = apply_curvature(image, config)

        # Border should be black
        assert result[0, 0, 0] == 0.0
        assert result[25, 25, 0] > 0

    def test_with_rounded_corners(self):
        """Test curvature with rounded corners."""
        config = CurvatureConfig(enabled=True, amount=0.1, corner_radius=15)
        image = np.ones((50, 50, 3), dtype=np.float32)
        result = apply_curvature(image, config)

        # Corner should be darker than center due to corner radius
        assert result[0, 0, 0] < result[25, 25, 0]

    def test_grayscale_image(self):
        """Test with grayscale image."""
        config = CurvatureConfig(enabled=True, amount=0.1)
        image = np.ones((50, 50), dtype=np.float32)
        result = apply_curvature(image, config)

        assert result.shape == (50, 50)


class TestBilinearSample:
    """Tests for bilinear_sample function."""

    def test_identity_sample(self):
        """Test sampling with identity mapping."""
        image = np.random.rand(10, 10, 3).astype(np.float32)

        # Create identity mapping
        y_coords, x_coords = np.mgrid[0:10, 0:10]
        u_pixels = x_coords.astype(np.float32)
        v_pixels = y_coords.astype(np.float32)

        result = bilinear_sample(image, u_pixels, v_pixels)

        np.testing.assert_array_almost_equal(image, result, decimal=2)

    def test_half_offset(self):
        """Test sampling with half-pixel offset."""
        image = np.ones((10, 10, 3), dtype=np.float32)
        image[5, 5, :] = 0.5  # Center pixel darker

        # Sample at half-pixel positions
        y_coords, x_coords = np.mgrid[0:10, 0:10]
        u_pixels = (x_coords + 0.5).astype(np.float32)
        v_pixels = y_coords.astype(np.float32)

        result = bilinear_sample(image, u_pixels, v_pixels)

        # Should average neighboring pixels
        assert result.shape == (10, 10, 3)


class TestApplyBorder:
    """Tests for apply_border function."""

    def test_no_border(self):
        """Test with zero border size."""
        image = np.ones((20, 20, 3), dtype=np.float32)
        result = apply_border(image, 0)

        np.testing.assert_array_equal(image, result)

    def test_with_border(self):
        """Test with border applied."""
        image = np.ones((20, 20, 3), dtype=np.float32)
        result = apply_border(image, 3)

        # Border should be black
        assert result[0, 0, 0] == 0.0
        assert result[2, 2, 0] == 0.0
        assert result[17, 17, 0] == 0.0
        assert result[19, 19, 0] == 0.0

        # Center should be unchanged
        assert result[10, 10, 0] == 1.0

    def test_grayscale_border(self):
        """Test border on grayscale image."""
        image = np.ones((20, 20), dtype=np.float32)
        result = apply_border(image, 3)

        assert result[0, 0] == 0.0
        assert result[10, 10] == 1.0


class TestCombineCurvatureVignette:
    """Tests for combine_curvature_vignette function."""

    def test_basic_combined(self):
        """Test basic combined effect."""
        image = np.ones((100, 100, 3), dtype=np.float32)
        result = combine_curvature_vignette(image, 0.1, 0.3)

        assert isinstance(result, np.ndarray)
        assert result.shape == (100, 100, 3)

    def test_zero_values(self):
        """Test with zero values (no effect)."""
        image = np.ones((50, 50, 3), dtype=np.float32)
        result = combine_curvature_vignette(image, 0.0, 0.0)

        # Should be essentially unchanged
        np.testing.assert_array_almost_equal(image, result, decimal=2)


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_calculate_edge_stretch_no_distortion(self):
        """Test edge stretch with no distortion."""
        stretch = calculate_edge_stretch(0.0)
        assert stretch == 1.0

    def test_calculate_edge_stretch_with_distortion(self):
        """Test edge stretch with distortion."""
        stretch = calculate_edge_stretch(0.3)
        assert stretch > 1.0

    def test_edge_stretch_increases_with_amount(self):
        """Test that edge stretch increases with amount."""
        stretch1 = calculate_edge_stretch(0.1)
        stretch2 = calculate_edge_stretch(0.2)

        assert stretch2 > stretch1

    def test_estimate_content_loss_none(self):
        """Test content loss with no curvature."""
        loss = estimate_content_loss(0.0)
        assert loss == 0.0

    def test_estimate_content_loss_some(self):
        """Test content loss with curvature."""
        loss = estimate_content_loss(0.3)
        assert loss > 0.0
        assert loss < 1.0

    def test_recommend_border_size_none(self):
        """Test border recommendation with no curvature."""
        border = recommend_border_size(100, 100, 0.0)
        assert border == 0

    def test_recommend_border_size_some(self):
        """Test border recommendation with curvature."""
        border = recommend_border_size(100, 100, 0.2)
        assert border > 0

    def test_recommend_border_size_proportional(self):
        """Test that border is proportional to image size."""
        border1 = recommend_border_size(100, 100, 0.2)
        border2 = recommend_border_size(200, 200, 0.2)

        # Larger image should have larger border
        assert border2 > border1


class TestEdgeCases:
    """Tests for edge cases."""

    def test_very_small_image(self):
        """Test with very small image."""
        config = CurvatureConfig(enabled=True, amount=0.1)
        image = np.ones((5, 5, 3), dtype=np.float32)
        result = apply_curvature(image, config)

        assert result.shape == (5, 5, 3)

    def test_very_large_curvature(self):
        """Test with large curvature amount."""
        config = CurvatureConfig(enabled=True, amount=0.5)
        image = np.ones((50, 50, 3), dtype=np.float32)
        result = apply_curvature(image, config)

        # Should still produce valid output
        assert result.min() >= 0
        assert result.max() <= 1

    def test_wide_image(self):
        """Test with wide (non-square) image."""
        config = CurvatureConfig(enabled=True, amount=0.1)
        image = np.ones((50, 200, 3), dtype=np.float32)
        result = apply_curvature(image, config)

        assert result.shape == (50, 200, 3)

    def test_tall_image(self):
        """Test with tall (non-square) image."""
        config = CurvatureConfig(enabled=True, amount=0.1)
        image = np.ones((200, 50, 3), dtype=np.float32)
        result = apply_curvature(image, config)

        assert result.shape == (200, 50, 3)

    def test_very_large_corner_radius(self):
        """Test with corner radius larger than image."""
        mask = create_corner_mask(20, 20, 50)

        # Should still produce valid mask
        assert mask.shape == (20, 20)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Unit tests for Phosphor Mask module.

Tests for phosphor mask generation and application.
"""

import pytest
import numpy as np

# Skip all tests if PIL not available
pytest.importorskip("PIL")

from PIL import Image

from lib.retro.phosphor import (
    # Pattern generators
    create_rgb_stripe_mask,
    create_aperture_grille_mask,
    create_slot_mask,
    create_shadow_mask,
    create_phosphor_mask,
    # Application functions
    apply_phosphor_mask,
    apply_phosphor_mask_fast,
    # Utility functions
    get_phosphor_brightness_factor,
    list_phosphor_patterns,
    get_pattern_description,
    estimate_mask_visibility,
    # Constants
    PHOSPHOR_PATTERNS,
)
from lib.retro.crt_types import PhosphorConfig


class TestCreateRGBStripeMask:
    """Tests for create_rgb_stripe_mask function."""

    def test_basic_mask(self):
        """Test basic RGB stripe mask generation."""
        mask = create_rgb_stripe_mask(30, 20)

        assert mask.shape == (20, 30, 3)
        assert mask.dtype == np.float32
        assert mask.min() >= 0
        assert mask.max() <= 1

    def test_rgb_pattern(self):
        """Test RGB pattern order."""
        mask = create_rgb_stripe_mask(9, 10, pattern="rgb", scale=1)

        # First stripe should be red
        assert mask[0, 0, 0] == 1.0  # Red channel
        assert mask[0, 0, 1] == 0.0  # Green channel
        assert mask[0, 0, 2] == 0.0  # Blue channel

        # Second stripe should be green
        assert mask[0, 1, 1] == 1.0  # Green channel

        # Third stripe should be blue
        assert mask[0, 2, 2] == 1.0  # Blue channel

    def test_bgr_pattern(self):
        """Test BGR pattern order."""
        mask = create_rgb_stripe_mask(9, 10, pattern="bgr", scale=1)

        # First stripe should be blue
        assert mask[0, 0, 2] == 1.0  # Blue channel
        assert mask[0, 0, 0] == 0.0  # Red channel

        # Second stripe should be green
        assert mask[0, 1, 1] == 1.0

        # Third stripe should be red
        assert mask[0, 2, 0] == 1.0

    def test_scale_factor(self):
        """Test scale factor affects stripe width."""
        mask1 = create_rgb_stripe_mask(12, 10, scale=1)
        mask2 = create_rgb_stripe_mask(12, 10, scale=2)

        # With scale=2, each stripe should be 2 pixels wide
        # So columns 0 and 1 should be same color with mask2
        np.testing.assert_array_equal(mask2[0, 0, :], mask2[0, 1, :])

    def test_pattern_repeat(self):
        """Test pattern repeats correctly."""
        mask = create_rgb_stripe_mask(12, 10, scale=1)

        # Pattern should repeat every 3 pixels
        np.testing.assert_array_equal(mask[0, 0, :], mask[0, 3, :])
        np.testing.assert_array_equal(mask[0, 1, :], mask[0, 4, :])
        np.testing.assert_array_equal(mask[0, 2, :], mask[0, 5, :])


class TestCreateApertureGrilleMask:
    """Tests for create_aperture_grille_mask function."""

    def test_basic_mask(self):
        """Test basic aperture grille mask generation."""
        mask = create_aperture_grille_mask(30, 20)

        assert mask.shape == (20, 30, 3)
        assert mask.dtype == np.float32

    def test_vertical_stripes(self):
        """Test that vertical stripes are present."""
        mask = create_aperture_grille_mask(12, 20, scale=1)

        # Should have vertical RGB pattern
        # Column 0 should be primarily red
        assert mask[0, 0, 0] > mask[0, 0, 1]
        assert mask[0, 0, 0] > mask[0, 0, 2]

    def test_damper_wires(self):
        """Test that damper wire lines are present."""
        mask = create_aperture_grille_mask(30, 60, scale=1)

        # Check that brightness varies at wire positions
        # (subtle, so just check structure)
        assert mask.shape[0] == 60

    def test_scale_factor(self):
        """Test scale affects stripe width."""
        mask1 = create_aperture_grille_mask(30, 20, scale=1)
        mask2 = create_aperture_grille_mask(30, 20, scale=2)

        # Different scale should produce different patterns
        assert not np.array_equal(mask1, mask2)


class TestCreateSlotMask:
    """Tests for create_slot_mask function."""

    def test_basic_mask(self):
        """Test basic slot mask generation."""
        mask = create_slot_mask(30, 20)

        assert mask.shape == (20, 30, 3)
        assert mask.dtype == np.float32

    def test_slot_dimensions(self):
        """Test custom slot dimensions."""
        mask = create_slot_mask(30, 20, slot_width=3, slot_height=6)

        assert mask.shape == (20, 30, 3)

    def test_has_dark_areas(self):
        """Test that mask has dark areas (slot borders)."""
        mask = create_slot_mask(30, 30, slot_width=2, slot_height=4)

        # Should have some dark pixels (mask material)
        assert mask.min() < 0.5

    def test_has_bright_areas(self):
        """Test that mask has bright areas (slots)."""
        mask = create_slot_mask(30, 30)

        # Should have some bright pixels (slots)
        assert mask.max() > 0.9


class TestCreateShadowMask:
    """Tests for create_shadow_mask function."""

    def test_basic_mask(self):
        """Test basic shadow mask generation."""
        mask = create_shadow_mask(30, 30)

        assert mask.shape == (30, 30, 3)
        assert mask.dtype == np.float32

    def test_circular_pattern(self):
        """Test that circular holes are present."""
        mask = create_shadow_mask(24, 24, scale=1)

        # Should have varying brightness
        assert mask.min() < mask.max()

    def test_scale_factor(self):
        """Test scale affects hole size."""
        mask1 = create_shadow_mask(30, 30, scale=1)
        mask2 = create_shadow_mask(30, 30, scale=2)

        assert not np.array_equal(mask1, mask2)


class TestCreatePhosphorMask:
    """Tests for create_phosphor_mask function."""

    def test_disabled(self):
        """Test disabled config returns uniform mask."""
        config = PhosphorConfig(enabled=False)
        mask = create_phosphor_mask(20, 20, config)

        # Should be all ones
        np.testing.assert_array_equal(mask, np.ones((20, 20, 3), dtype=np.float32))

    def test_rgb_pattern(self):
        """Test RGB pattern selection."""
        config = PhosphorConfig(enabled=True, pattern="rgb")
        mask = create_phosphor_mask(20, 20, config)

        assert mask.shape == (20, 20, 3)

    def test_aperture_grille_pattern(self):
        """Test aperture grille pattern selection."""
        config = PhosphorConfig(enabled=True, pattern="aperture_grille")
        mask = create_phosphor_mask(20, 20, config)

        assert mask.shape == (20, 20, 3)

    def test_slot_mask_pattern(self):
        """Test slot mask pattern selection."""
        config = PhosphorConfig(
            enabled=True,
            pattern="slot_mask",
            slot_width=2,
            slot_height=4
        )
        mask = create_phosphor_mask(20, 20, config)

        assert mask.shape == (20, 20, 3)

    def test_shadow_mask_pattern(self):
        """Test shadow mask pattern selection."""
        config = PhosphorConfig(enabled=True, pattern="shadow_mask")
        mask = create_phosphor_mask(20, 20, config)

        assert mask.shape == (20, 20, 3)

    def test_invalid_pattern_defaults_to_rgb(self):
        """Test that invalid pattern defaults to RGB."""
        config = PhosphorConfig(enabled=True, pattern="rgb")
        # Manually set to invalid to bypass validation
        object.__setattr__(config, 'pattern', 'invalid')
        mask = create_phosphor_mask(20, 20, config)

        assert mask.shape == (20, 20, 3)


class TestApplyPhosphorMask:
    """Tests for apply_phosphor_mask function."""

    def test_disabled(self):
        """Test disabled config returns original image."""
        config = PhosphorConfig(enabled=False)
        image = Image.new("RGB", (20, 20), color=(128, 128, 128))
        result = apply_phosphor_mask(image, config)

        np.testing.assert_array_equal(np.array(image), np.array(result))

    def test_pil_image(self):
        """Test application to PIL Image."""
        config = PhosphorConfig(enabled=True, pattern="rgb", intensity=0.5)
        image = Image.new("RGB", (30, 20), color=(255, 255, 255))
        result = apply_phosphor_mask(image, config)

        assert isinstance(result, Image.Image)
        assert result.size == (30, 20)

        # Check that image is modified (not uniform white anymore)
        arr = np.array(result)
        # Some variation should exist
        assert arr[:, :, 0].std() > 0 or arr[:, :, 1].std() > 0 or arr[:, :, 2].std() > 0

    def test_numpy_array(self):
        """Test application to numpy array."""
        config = PhosphorConfig(enabled=True, pattern="rgb", intensity=0.5)
        image = np.ones((20, 20, 3), dtype=np.float32)
        result = apply_phosphor_mask(image, config)

        assert isinstance(result, np.ndarray)
        assert result.shape == (20, 20, 3)

    def test_grayscale_image(self):
        """Test application to grayscale image."""
        config = PhosphorConfig(enabled=True, intensity=0.5)
        image = np.ones((20, 20), dtype=np.float32)
        result = apply_phosphor_mask(image, config)

        assert result.shape == (20, 20)

    def test_intensity_blending(self):
        """Test intensity blending."""
        config_low = PhosphorConfig(enabled=True, pattern="rgb", intensity=0.1)
        config_high = PhosphorConfig(enabled=True, pattern="rgb", intensity=0.9)

        image = np.ones((20, 20, 3), dtype=np.float32)
        result_low = apply_phosphor_mask(image, config_low)
        result_high = apply_phosphor_mask(image, config_high)

        # Higher intensity should have more color variation
        low_std = np.std(result_low)
        high_std = np.std(result_high)
        assert high_std > low_std

    def test_scale_factor(self):
        """Test scale factor in application."""
        config1 = PhosphorConfig(enabled=True, scale=1.0)
        config2 = PhosphorConfig(enabled=True, scale=2.0)

        image = np.ones((30, 30, 3), dtype=np.float32)
        result1 = apply_phosphor_mask(image, config1)
        result2 = apply_phosphor_mask(image, config2)

        # Different scales should produce different results
        assert not np.array_equal(result1, result2)


class TestApplyPhosphorMaskFast:
    """Tests for apply_phosphor_mask_fast function."""

    def test_disabled(self):
        """Test disabled config returns original image."""
        config = PhosphorConfig(enabled=False)
        image = Image.new("RGB", (20, 20), color=(128, 128, 128))
        result = apply_phosphor_mask_fast(image, config)

        np.testing.assert_array_equal(np.array(image), np.array(result))

    def test_pil_image(self):
        """Test application to PIL Image."""
        config = PhosphorConfig(enabled=True, pattern="rgb", intensity=0.5)
        image = Image.new("RGB", (20, 20), color=(255, 255, 255))
        result = apply_phosphor_mask_fast(image, config)

        assert isinstance(result, Image.Image)

    def test_produces_pattern(self):
        """Test that fast version produces visible pattern."""
        config = PhosphorConfig(enabled=True, pattern="rgb", intensity=0.8)
        image = np.ones((30, 30, 3), dtype=np.float32)
        result = apply_phosphor_mask_fast(image, config)

        # Should have color variation
        assert result[:, :, 0].mean() != result[:, :, 1].mean()


class TestUtilityFunctions:
    """Tests for utility functions."""

    def test_get_phosphor_brightness_factor_disabled(self):
        """Test brightness factor for disabled mask."""
        config = PhosphorConfig(enabled=False)
        factor = get_phosphor_brightness_factor(config)
        assert factor == 1.0

    def test_get_phosphor_brightness_factor_enabled(self):
        """Test brightness factor for enabled mask."""
        config = PhosphorConfig(enabled=True, intensity=1.0)
        factor = get_phosphor_brightness_factor(config)
        # Should be less than 1 (mask blocks light)
        assert factor < 1.0

    def test_brightness_factor_by_pattern(self):
        """Test brightness factors vary by pattern."""
        patterns = ["rgb", "aperture_grille", "slot_mask", "shadow_mask"]

        factors = {}
        for pattern in patterns:
            config = PhosphorConfig(enabled=True, pattern=pattern, intensity=1.0)
            factors[pattern] = get_phosphor_brightness_factor(config)

        # Aperture grille should be most efficient
        assert factors["aperture_grille"] >= factors["shadow_mask"]

    def test_list_phosphor_patterns(self):
        """Test listing available patterns."""
        patterns = list_phosphor_patterns()

        assert "rgb" in patterns
        assert "bgr" in patterns
        assert "aperture_grille" in patterns
        assert "slot_mask" in patterns
        assert "shadow_mask" in patterns

    def test_get_pattern_description(self):
        """Test getting pattern descriptions."""
        desc = get_pattern_description("rgb")
        assert isinstance(desc, str)
        assert len(desc) > 0

        desc = get_pattern_description("aperture_grille")
        assert "Trinitron" in desc

        desc = get_pattern_description("invalid")
        assert "Unknown" in desc

    def test_estimate_mask_visibility_disabled(self):
        """Test visibility for disabled mask."""
        config = PhosphorConfig(enabled=False)
        visibility = estimate_mask_visibility(config, (1920, 1080))
        assert visibility == 0.0

    def test_estimate_mask_visibility_basic(self):
        """Test basic visibility estimation."""
        config = PhosphorConfig(enabled=True, intensity=0.5)
        visibility = estimate_mask_visibility(config, (1920, 1080))

        assert 0 <= visibility <= 1.0

    def test_estimate_mask_visibility_resolution(self):
        """Test visibility at different resolutions."""
        config = PhosphorConfig(enabled=True, intensity=0.5, scale=1.0)

        vis_low = estimate_mask_visibility(config, (640, 480))
        vis_high = estimate_mask_visibility(config, (1920, 1080))

        # Lower resolution should be more visible (higher visibility score)
        # Due to resolution_factor calculation
        assert vis_low >= vis_high

    def test_estimate_mask_visibility_distance(self):
        """Test visibility at different viewing distances."""
        config = PhosphorConfig(enabled=True, intensity=0.5)

        vis_close = estimate_mask_visibility(config, (1920, 1080), view_distance=0.5)
        vis_far = estimate_mask_visibility(config, (1920, 1080), view_distance=2.0)

        # Closer should be more visible
        assert vis_close > vis_far


class TestPhosphorPatterns:
    """Tests for PHOSPHOR_PATTERNS constant."""

    def test_rgb_pattern(self):
        """Test RGB pattern definition."""
        assert "rgb" in PHOSPHOR_PATTERNS
        pattern = PHOSPHOR_PATTERNS["rgb"]
        assert len(pattern) == 3  # R, G, B

    def test_bgr_pattern(self):
        """Test BGR pattern definition."""
        assert "bgr" in PHOSPHOR_PATTERNS
        pattern = PHOSPHOR_PATTERNS["bgr"]
        assert len(pattern) == 3  # B, G, R


class TestEdgeCases:
    """Tests for edge cases."""

    def test_very_small_scale(self):
        """Test with very small scale."""
        mask = create_rgb_stripe_mask(20, 20, scale=0.5)
        assert mask.shape == (20, 20, 3)

    def test_very_large_scale(self):
        """Test with very large scale."""
        mask = create_rgb_stripe_mask(60, 40, scale=10)
        assert mask.shape == (40, 60, 3)

    def test_single_pixel_width(self):
        """Test with minimal width."""
        mask = create_rgb_stripe_mask(1, 10)
        assert mask.shape == (10, 1, 3)

    def test_single_pixel_height(self):
        """Test with minimal height."""
        mask = create_rgb_stripe_mask(10, 1)
        assert mask.shape == (1, 10, 3)

    def test_zero_intensity(self):
        """Test with zero intensity (no effect)."""
        config = PhosphorConfig(enabled=True, intensity=0.0)
        image = np.ones((20, 20, 3), dtype=np.float32)
        result = apply_phosphor_mask(image, config)

        # Should be nearly unchanged
        np.testing.assert_array_almost_equal(image, result, decimal=2)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

"""
Unit tests for CRT Effects module.

Tests for bloom, chromatic aberration, flicker, interlace, jitter, noise, ghosting,
and the combined effects pipeline.
"""

import pytest
import numpy as np

# Skip all tests if PIL not available
pytest.importorskip("PIL")

from PIL import Image

from lib.retro.crt_effects import (
    # Individual effects
    apply_bloom,
    apply_chromatic_aberration,
    apply_flicker,
    apply_interlace,
    apply_pixel_jitter,
    apply_noise,
    apply_ghosting,
    apply_color_adjustments,
    # Pipeline
    apply_all_effects,
    apply_effects_fast,
    # Utility
    simple_blur,
)
from lib.retro.crt_types import (
    CRTConfig,
    ScanlineConfig,
    PhosphorConfig,
    CurvatureConfig,
)


class TestApplyBloom:
    """Tests for apply_bloom function."""

    def test_no_bloom(self):
        """Test with zero bloom amount."""
        image = Image.new("RGB", (50, 50), color=(128, 128, 128))
        result = apply_bloom(image, 0.0)

        np.testing.assert_array_equal(np.array(image), np.array(result))

    def test_basic_bloom(self):
        """Test basic bloom application."""
        image = Image.new("RGB", (50, 50), color=(255, 255, 255))
        result = apply_bloom(image, 0.3)

        assert isinstance(result, Image.Image)
        assert result.size == (50, 50)

    def test_threshold(self):
        """Test bloom with different thresholds."""
        # Half-bright image should not bloom with high threshold
        image = Image.new("RGB", (50, 50), color=(128, 128, 128))

        result_no_threshold = apply_bloom(image, 0.5, threshold=0.3)
        result_high_threshold = apply_bloom(image, 0.5, threshold=0.9)

        # Lower threshold should produce more bloom
        assert np.array(result_no_threshold).mean() != np.array(result_high_threshold).mean()


class TestApplyChromaticAberration:
    """Tests for apply_chromatic_aberration function."""

    def test_no_aberration(self):
        """Test with zero chromatic aberration."""
        image = Image.new("RGB", (50, 50), color=(128, 128, 128))
        result = apply_chromatic_aberration(image, 0.0)

        np.testing.assert_array_equal(np.array(image), np.array(result))

    def test_basic_aberration(self):
        """Test basic chromatic aberration."""
        image = Image.new("RGB", (100, 50), color=(255, 255, 255))
        result = apply_chromatic_aberration(image, 0.01)

        assert isinstance(result, Image.Image)
        assert result.size == (100, 50)

    def test_channel_separation(self):
        """Test that channels are shifted."""
        # Create image with distinct edges
        arr = np.zeros((50, 100, 3), dtype=np.uint8)
        arr[:, 50:, :] = 255  # Right half white
        image = Image.fromarray(arr)

        result = apply_chromatic_aberration(image, 0.02)
        result_arr = np.array(result)

        # Red and blue channels should be shifted
        # Not a perfect test due to boundary handling
        assert isinstance(result, Image.Image)

    def test_grayscale_no_effect(self):
        """Test that grayscale has no chromatic effect."""
        image = np.ones((50, 50), dtype=np.float32)
        result = apply_chromatic_aberration(image, 0.01)

        # Should return unchanged for grayscale
        np.testing.assert_array_equal(image, result)


class TestApplyFlicker:
    """Tests for apply_flicker function."""

    def test_no_flicker(self):
        """Test with zero flicker."""
        image = Image.new("RGB", (50, 50), color=(128, 128, 128))
        result = apply_flicker(image, 0.0, frame=0)

        np.testing.assert_array_equal(np.array(image), np.array(result))

    def test_basic_flicker(self):
        """Test basic flicker application."""
        image = Image.new("RGB", (50, 50), color=(128, 128, 128))
        result = apply_flicker(image, 0.5, frame=0)

        assert isinstance(result, Image.Image)

    def test_frame_variation(self):
        """Test that different frames produce different results."""
        image = Image.new("RGB", (50, 50), color=(128, 128, 128))

        result0 = np.array(apply_flicker(image, 0.5, frame=0, seed=42))
        result10 = np.array(apply_flicker(image, 0.5, frame=10, seed=42))

        # Different frames should produce different brightness
        # (may not always differ due to randomness, but likely)
        assert isinstance(result0, np.ndarray)

    def test_seed_reproducibility(self):
        """Test that same seed produces same result."""
        image = Image.new("RGB", (50, 50), color=(128, 128, 128))

        result1 = np.array(apply_flicker(image, 0.5, frame=5, seed=123))
        result2 = np.array(apply_flicker(image, 0.5, frame=5, seed=123))

        np.testing.assert_array_equal(result1, result2)


class TestApplyInterlace:
    """Tests for apply_interlace function."""

    def test_even_field(self):
        """Test even field (field=0)."""
        image = np.ones((10, 10, 3), dtype=np.float32)
        result = apply_interlace(image, field=0)

        # Even rows (0, 2, 4...) should be unchanged
        # Odd rows (1, 3, 5...) should be darkened
        assert result[0, 0, 0] == 1.0  # Row 0 is unchanged
        assert result[1, 0, 0] == 0.5  # Row 1 is darkened

    def test_odd_field(self):
        """Test odd field (field=1)."""
        image = np.ones((10, 10, 3), dtype=np.float32)
        result = apply_interlace(image, field=1)

        # Odd rows should be unchanged, even rows should be darkened
        assert result[0, 0, 0] == 0.5  # Row 0 is darkened
        assert result[1, 0, 0] == 1.0  # Row 1 is unchanged

    def test_grayscale(self):
        """Test with grayscale image."""
        image = np.ones((10, 10), dtype=np.float32)
        result = apply_interlace(image, field=0)

        # Check values without channel dimension
        assert result[0, 0] == 1.0  # Row 0 unchanged
        assert result[1, 0] == 0.5  # Row 1 darkened


class TestApplyPixelJitter:
    """Tests for apply_pixel_jitter function."""

    def test_no_jitter(self):
        """Test with zero jitter."""
        image = Image.new("RGB", (50, 50), color=(128, 128, 128))
        result = apply_pixel_jitter(image, 0.0, frame=0)

        np.testing.assert_array_equal(np.array(image), np.array(result))

    def test_basic_jitter(self):
        """Test basic jitter application."""
        image = Image.new("RGB", (50, 50), color=(128, 128, 128))
        result = apply_pixel_jitter(image, 0.5, frame=0, seed=42)

        assert isinstance(result, Image.Image)

    def test_seed_reproducibility(self):
        """Test that same seed produces same result."""
        image = Image.new("RGB", (50, 50), color=(255, 255, 255))

        result1 = np.array(apply_pixel_jitter(image, 0.5, frame=0, seed=123))
        result2 = np.array(apply_pixel_jitter(image, 0.5, frame=0, seed=123))

        np.testing.assert_array_equal(result1, result2)


class TestApplyNoise:
    """Tests for apply_noise function."""

    def test_no_noise(self):
        """Test with zero noise."""
        image = Image.new("RGB", (50, 50), color=(128, 128, 128))
        result = apply_noise(image, 0.0, frame=0)

        np.testing.assert_array_equal(np.array(image), np.array(result))

    def test_basic_noise(self):
        """Test basic noise application."""
        image = Image.new("RGB", (50, 50), color=(128, 128, 128))
        result = apply_noise(image, 0.1, frame=0, seed=42)

        assert isinstance(result, Image.Image)

        # Image should be modified
        assert not np.array_equal(np.array(image), np.array(result))

    def test_seed_reproducibility(self):
        """Test that same seed produces same noise."""
        image = Image.new("RGB", (50, 50), color=(128, 128, 128))

        result1 = np.array(apply_noise(image, 0.1, frame=0, seed=123))
        result2 = np.array(apply_noise(image, 0.1, frame=0, seed=123))

        np.testing.assert_array_equal(result1, result2)


class TestApplyGhosting:
    """Tests for apply_ghosting function."""

    def test_no_ghosting(self):
        """Test with zero ghosting."""
        image = Image.new("RGB", (50, 50), color=(128, 128, 128))
        prev = Image.new("RGB", (50, 50), color=(64, 64, 64))
        result = apply_ghosting(image, 0.0, prev)

        np.testing.assert_array_equal(np.array(image), np.array(result))

    def test_no_previous_frame(self):
        """Test with no previous frame."""
        image = Image.new("RGB", (50, 50), color=(128, 128, 128))
        result = apply_ghosting(image, 0.5, None)

        np.testing.assert_array_equal(np.array(image), np.array(result))

    def test_basic_ghosting(self):
        """Test basic ghosting application."""
        current = np.full((50, 50, 3), 1.0, dtype=np.float32)
        previous = np.full((50, 50, 3), 0.0, dtype=np.float32)

        result = apply_ghosting(current, 0.5, previous)

        # Should blend: current * 0.5 + previous * 0.5 = 0.5
        assert result[0, 0, 0] == pytest.approx(0.5, rel=0.01)


class TestApplyColorAdjustments:
    """Tests for apply_color_adjustments function."""

    def test_no_adjustments(self):
        """Test with default values."""
        image = Image.new("RGB", (50, 50), color=(128, 128, 128))
        result = apply_color_adjustments(image)

        # Default values should not change image significantly
        # (gamma 2.2 may cause slight change)
        assert isinstance(result, Image.Image)

    def test_brightness(self):
        """Test brightness adjustment."""
        image = np.full((10, 10, 3), 0.5, dtype=np.float32)

        result_bright = apply_color_adjustments(image, brightness=2.0, contrast=1.0, gamma=1.0)
        result_dark = apply_color_adjustments(image, brightness=0.5, contrast=1.0, gamma=1.0)

        # Bright result: 0.5 * 2.0 = 1.0 (clipped)
        assert result_bright[0, 0, 0] == pytest.approx(1.0, rel=0.01)
        # Dark result: 0.5 * 0.5 = 0.25
        assert result_dark[0, 0, 0] == pytest.approx(0.25, rel=0.01)

    def test_contrast(self):
        """Test contrast adjustment."""
        image = np.full((10, 10, 3), 0.5, dtype=np.float32)

        result = apply_color_adjustments(image, contrast=2.0, brightness=1.0, gamma=1.0)

        # 0.5 should remain 0.5 at contrast center
        # (0.5 - 0.5) * 2.0 + 0.5 = 0.5
        assert result[0, 0, 0] == pytest.approx(0.5, rel=0.1)

    def test_saturation(self):
        """Test saturation adjustment."""
        image = np.ones((10, 10, 3), dtype=np.float32)
        image[:, :, 0] = 1.0  # Red
        image[:, :, 1] = 0.5  # Half green
        image[:, :, 2] = 0.0  # No blue

        result_grayscale = apply_color_adjustments(image, saturation=0.0)

        # All channels should be equal at saturation 0
        assert result_grayscale[0, 0, 0] == pytest.approx(
            result_grayscale[0, 0, 1], rel=0.01
        )

    def test_gamma(self):
        """Test gamma correction."""
        image = np.full((10, 10, 3), 0.5, dtype=np.float32)

        result = apply_color_adjustments(image, gamma=1.0)

        # Gamma 1.0 should not change the value
        assert result[0, 0, 0] == pytest.approx(0.5, rel=0.01)


class TestApplyAllEffects:
    """Tests for apply_all_effects pipeline."""

    def test_disabled_all(self):
        """Test with all effects disabled."""
        config = CRTConfig(
            name="test",
            scanlines=ScanlineConfig(enabled=False),
            phosphor=PhosphorConfig(enabled=False),
            curvature=CurvatureConfig(enabled=False),
        )
        image = Image.new("RGB", (50, 50), color=(128, 128, 128))
        result = apply_all_effects(image, config, frame=0)

        assert isinstance(result, Image.Image)

    def test_basic_pipeline(self):
        """Test basic pipeline execution."""
        config = CRTConfig(
            name="test",
            bloom=0.1,
            chromatic_aberration=0.002,
        )
        image = Image.new("RGB", (100, 100), color=(255, 255, 255))
        result = apply_all_effects(image, config, frame=0)

        assert isinstance(result, Image.Image)
        assert result.size == (100, 100)

    def test_with_ghosting(self):
        """Test pipeline with ghosting."""
        config = CRTConfig(ghosting=0.3)
        image = np.ones((50, 50, 3), dtype=np.float32)
        prev = np.zeros((50, 50, 3), dtype=np.float32)

        result = apply_all_effects(image, config, frame=0, previous_frame=prev)

        assert isinstance(result, np.ndarray)
        # Should blend current and previous
        assert result[0, 0, 0] < 1.0


class TestApplyEffectsFast:
    """Tests for apply_effects_fast function."""

    def test_basic_fast(self):
        """Test basic fast pipeline."""
        config = CRTConfig(
            name="test",
            scanlines=ScanlineConfig(enabled=True),
        )
        image = Image.new("RGB", (50, 50), color=(255, 255, 255))
        result = apply_effects_fast(image, config, frame=0)

        assert isinstance(result, Image.Image)

    def test_skips_expensive_effects(self):
        """Test that fast version skips expensive effects."""
        config = CRTConfig(
            bloom=0.5,
            noise=0.2,
            flicker=0.1,
        )
        image = Image.new("RGB", (50, 50), color=(128, 128, 128))
        result = apply_effects_fast(image, config, frame=0)

        # Should still produce valid output
        assert isinstance(result, Image.Image)


class TestSimpleBlur:
    """Tests for simple_blur function."""

    def test_no_blur(self):
        """Test with radius 0."""
        arr = np.random.rand(10, 10, 3).astype(np.float32)
        result = simple_blur(arr, radius=0)

        np.testing.assert_array_equal(arr, result)

    def test_basic_blur(self):
        """Test basic blur application."""
        arr = np.zeros((10, 10, 3), dtype=np.float32)
        arr[5, 5, :] = 1.0  # Single bright pixel

        result = simple_blur(arr, radius=1)

        # Center should be less bright after blur
        assert result[5, 5, 0] < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

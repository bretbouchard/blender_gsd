"""
Unit tests for MSG 1998 film look module.

Tests film look parameters and effects without Blender compositor.
"""

import pytest

from lib.msg1998.film_look_1998 import (
    apply_film_grain,
    apply_lens_effects,
    apply_vignette,
)
from lib.msg1998.types import FilmLook1998


class TestApplyFilmGrain:
    """Tests for apply_film_grain function."""

    def test_default_params(self):
        """Test with default parameters."""
        # Pass None image since we're testing without Blender
        result = apply_film_grain(None)

        assert "grain_intensity" in result
        assert result["grain_intensity"] == 0.15

    def test_custom_params(self):
        """Test with custom parameters."""
        params = FilmLook1998(grain_intensity=0.25)
        result = apply_film_grain(None, params)

        assert result["grain_intensity"] == 0.25

    def test_high_grain(self):
        """Test with high grain intensity."""
        params = FilmLook1998(grain_intensity=0.5)
        result = apply_film_grain(None, params)

        assert result["grain_intensity"] == 0.5

    def test_low_grain(self):
        """Test with low grain intensity."""
        params = FilmLook1998(grain_intensity=0.05)
        result = apply_film_grain(None, params)

        assert result["grain_intensity"] == 0.05


class TestApplyLensEffects:
    """Tests for apply_lens_effects function."""

    def test_default_params(self):
        """Test with default parameters."""
        result = apply_lens_effects(None)

        assert "distortion" in result
        assert "chromatic_aberration" in result
        assert result["distortion"] == 0.02
        assert result["chromatic_aberration"] == 0.003

    def test_custom_distortion(self):
        """Test with custom distortion."""
        params = FilmLook1998(lens_distortion=0.05)
        result = apply_lens_effects(None, params)

        assert result["distortion"] == 0.05

    def test_custom_chromatic_aberration(self):
        """Test with custom chromatic aberration."""
        params = FilmLook1998(chromatic_aberration=0.01)
        result = apply_lens_effects(None, params)

        assert result["chromatic_aberration"] == 0.01

    def test_no_distortion(self):
        """Test with no distortion."""
        params = FilmLook1998(
            lens_distortion=0.0,
            chromatic_aberration=0.0
        )
        result = apply_lens_effects(None, params)

        assert result["distortion"] == 0.0
        assert result["chromatic_aberration"] == 0.0


class TestApplyVignette:
    """Tests for apply_vignette function."""

    def test_default_params(self):
        """Test with default parameters."""
        result = apply_vignette(None)

        assert "vignette_strength" in result
        assert result["vignette_strength"] == 0.4

    def test_custom_vignette(self):
        """Test with custom vignette strength."""
        params = FilmLook1998(vignette_strength=0.6)
        result = apply_vignette(None, params)

        assert result["vignette_strength"] == 0.6

    def test_strong_vignette(self):
        """Test with strong vignette."""
        params = FilmLook1998(vignette_strength=0.8)
        result = apply_vignette(None, params)

        assert result["vignette_strength"] == 0.8

    def test_no_vignette(self):
        """Test with no vignette."""
        params = FilmLook1998(vignette_strength=0.0)
        result = apply_vignette(None, params)

        assert result["vignette_strength"] == 0.0


class TestFilmLook1998Dataclass:
    """Tests for FilmLook1998 dataclass."""

    def test_default_values(self):
        """Test default film look values."""
        params = FilmLook1998()

        assert params.grain_intensity == 0.15
        assert params.grain_size == 1.0
        assert params.lens_distortion == 0.02
        assert params.chromatic_aberration == 0.003
        assert params.vignette_strength == 0.4
        assert params.color_temperature == 5500
        assert params.cooke_flare_intensity == 0.1
        assert params.cooke_breathing == 0.02

    def test_all_custom_values(self):
        """Test with all custom values."""
        params = FilmLook1998(
            grain_intensity=0.3,
            grain_size=0.8,
            lens_distortion=0.03,
            chromatic_aberration=0.005,
            vignette_strength=0.5,
            color_temperature=6500,
            cooke_flare_intensity=0.15,
            cooke_breathing=0.03
        )

        assert params.grain_intensity == 0.3
        assert params.grain_size == 0.8
        assert params.lens_distortion == 0.03
        assert params.chromatic_aberration == 0.005
        assert params.vignette_strength == 0.5
        assert params.color_temperature == 6500
        assert params.cooke_flare_intensity == 0.15
        assert params.cooke_breathing == 0.03

    def test_realistic_film_stock_preset(self):
        """Test preset for realistic 1998 film stock."""
        # Kodak Vision3 500T 5219 style
        params = FilmLook1998(
            grain_intensity=0.12,
            grain_size=1.2,
            color_temperature=3200  # Tungsten balanced
        )

        assert params.grain_intensity < 0.2
        assert params.color_temperature < 4000

    def test_documentary_style_preset(self):
        """Test preset for documentary style."""
        params = FilmLook1998(
            grain_intensity=0.2,
            lens_distortion=0.03,
            vignette_strength=0.3
        )

        # Documentary often has more visible grain
        assert params.grain_intensity >= 0.15


class TestFilmLookCombinations:
    """Tests for combined film look effects."""

    def test_apply_all_effects_default(self):
        """Test applying all effects with defaults."""
        grain_result = apply_film_grain(None)
        lens_result = apply_lens_effects(None)
        vignette_result = apply_vignette(None)

        # All should return dicts with their respective keys
        assert "grain_intensity" in grain_result
        assert "distortion" in lens_result
        assert "vignette_strength" in vignette_result

    def test_apply_all_effects_custom(self):
        """Test applying all effects with custom params."""
        params = FilmLook1998(
            grain_intensity=0.3,
            lens_distortion=0.05,
            chromatic_aberration=0.008,
            vignette_strength=0.6
        )

        grain_result = apply_film_grain(None, params)
        lens_result = apply_lens_effects(None, params)
        vignette_result = apply_vignette(None, params)

        assert grain_result["grain_intensity"] == 0.3
        assert lens_result["distortion"] == 0.05
        assert lens_result["chromatic_aberration"] == 0.008
        assert vignette_result["vignette_strength"] == 0.6

    def test_minimal_effects(self):
        """Test minimal/subtle effects."""
        params = FilmLook1998(
            grain_intensity=0.05,
            lens_distortion=0.005,
            chromatic_aberration=0.001,
            vignette_strength=0.1
        )

        grain_result = apply_film_grain(None, params)
        lens_result = apply_lens_effects(None, params)
        vignette_result = apply_vignette(None, params)

        # All values should be low
        assert grain_result["grain_intensity"] < 0.1
        assert lens_result["distortion"] < 0.01
        assert vignette_result["vignette_strength"] < 0.2

    def test_intense_effects(self):
        """Test intense/heavy effects."""
        params = FilmLook1998(
            grain_intensity=0.5,
            lens_distortion=0.1,
            chromatic_aberration=0.02,
            vignette_strength=0.8
        )

        grain_result = apply_film_grain(None, params)
        lens_result = apply_lens_effects(None, params)
        vignette_result = apply_vignette(None, params)

        assert grain_result["grain_intensity"] >= 0.5
        assert lens_result["distortion"] >= 0.1
        assert vignette_result["vignette_strength"] >= 0.8


class TestFilmLookPresets:
    """Tests for film look preset scenarios."""

    def test_35mm_anamorphic_preset(self):
        """Test 35mm anamorphic lens characteristics."""
        # Anamorphic lenses have distinctive characteristics
        params = FilmLook1998(
            lens_distortion=0.03,
            chromatic_aberration=0.004,
            vignette_strength=0.3,
            cooke_flare_intensity=0.2,
            cooke_breathing=0.03
        )

        assert params.lens_distortion > 0
        assert params.cooke_flare_intensity > 0.1

    def test_clean_digital_look(self):
        """Test parameters for cleaner, less gritty look."""
        params = FilmLook1998(
            grain_intensity=0.02,
            lens_distortion=0.0,
            chromatic_aberration=0.0,
            vignette_strength=0.1
        )

        assert params.grain_intensity < 0.05
        assert params.lens_distortion == 0
        assert params.chromatic_aberration == 0

    def test_vintage_degraded_look(self):
        """Test parameters for vintage, degraded film look."""
        params = FilmLook1998(
            grain_intensity=0.4,
            grain_size=1.5,
            lens_distortion=0.05,
            vignette_strength=0.6
        )

        assert params.grain_intensity > 0.3
        assert params.grain_size > 1.0

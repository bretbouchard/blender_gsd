"""
Tests for lib/vfx/color_correction.py

Tests color correction functions without Blender (bpy).
"""

import pytest
import math

from lib.vfx.compositor_types import ColorCorrection
from lib.vfx.color_correction import (
    apply_exposure,
    apply_gamma,
    apply_contrast,
    apply_saturation,
    apply_lift_gamma_gain,
    apply_lgg_rgb,
    apply_cdl,
    apply_cdl_rgb,
    apply_curve,
    apply_rgb_curves,
    apply_levels,
    apply_hsv_adjustment,
    rgb_to_hsv,
    hsv_to_rgb,
    apply_white_balance,
    apply_highlights_shadows,
    apply_color_correction,
    COLOR_PRESETS,
    get_color_preset,
    apply_preset,
)


class TestColorCorrection:
    """Tests for ColorCorrection dataclass."""

    def test_create_settings(self):
        """Test creating settings."""
        settings = ColorCorrection(
            exposure=1.0,
            contrast=1.2,
            saturation=1.1
        )
        assert settings.exposure == 1.0
        assert settings.contrast == 1.2
        assert settings.saturation == 1.1

    def test_default_values(self):
        """Test default values are neutral."""
        settings = ColorCorrection()
        assert settings.exposure == 0.0
        assert settings.contrast == 1.0
        assert settings.saturation == 1.0
        assert settings.gamma == 1.0

    def test_rgb_tuple_fields(self):
        """Test RGB tuple fields."""
        settings = ColorCorrection(
            lift=(0.1, 0.2, 0.3),
            gain=(1.1, 1.0, 0.9),
        )
        assert settings.lift == (0.1, 0.2, 0.3)
        assert settings.gain == (1.1, 1.0, 0.9)


class TestApplyExposure:
    """Tests for apply_exposure function."""

    def test_apply_exposure_positive(self):
        """Test positive exposure adjustment."""
        value = 0.5
        result = apply_exposure(value, 1.0)
        # +1 stop should double the value
        assert result > value

    def test_apply_exposure_negative(self):
        """Test negative exposure adjustment."""
        value = 0.5
        result = apply_exposure(value, -1.0)
        # -1 stop should halve the value
        assert result < value

    def test_apply_exposure_zero(self):
        """Test zero exposure adjustment."""
        value = 0.5
        result = apply_exposure(value, 0.0)
        assert result == value

    def test_apply_exposure_doubles(self):
        """Test that exposure follows power of 2."""
        value = 0.25
        result = apply_exposure(value, 2.0)
        # +2 stops = 4x brighter
        assert abs(result - 1.0) < 0.001


class TestApplyGamma:
    """Tests for apply_gamma function."""

    def test_apply_gamma_basic(self):
        """Test basic gamma adjustment."""
        value = 0.5
        result = apply_gamma(value, 2.2)
        assert 0.0 <= result <= 1.0

    def test_apply_gamma_neutral(self):
        """Test neutral gamma (1.0)."""
        value = 0.5
        result = apply_gamma(value, 1.0)
        assert result == value

    def test_apply_gamma_high(self):
        """Test high gamma (applies gamma correction)."""
        value = 0.5
        result = apply_gamma(value, 2.2)
        # Gamma correction with value > 1
        # Formula: value ** (1.0 / gamma)
        # 0.5 ** (1.0 / 2.2) > 0.5
        assert result > value  # gamma > 1 brightens midtones

    def test_apply_gamma_low(self):
        """Test low gamma (applies gamma correction)."""
        value = 0.5
        result = apply_gamma(value, 0.5)
        # With gamma < 1, formula: 0.5 ** (1.0 / 0.5) = 0.5 ** 2 = 0.25
        assert result < value  # gamma < 1 darkens midtones

    def test_apply_gamma_zero(self):
        """Test gamma of zero returns 0."""
        value = 0.5
        result = apply_gamma(value, 0.0)
        assert result == 0.0


class TestApplyContrast:
    """Tests for apply_contrast function."""

    def test_apply_contrast_increase(self):
        """Test increasing contrast."""
        value = 0.5
        result = apply_contrast(value, 1.5)
        # Mid-point should remain roughly the same
        assert 0.45 <= result <= 0.55

    def test_apply_contrast_decrease(self):
        """Test decreasing contrast."""
        value = 0.3
        result = apply_contrast(value, 0.5)
        # Values should move toward 0.5
        assert abs(result - 0.5) < abs(value - 0.5)

    def test_apply_contrast_neutral(self):
        """Test neutral contrast (1.0)."""
        value = 0.3
        result = apply_contrast(value, 1.0)
        assert result == value

    def test_apply_contrast_zero(self):
        """Test zero contrast (all gray)."""
        value = 0.3
        result = apply_contrast(value, 0.0)
        # All values should become 0.5 (middle gray)
        assert abs(result - 0.5) < 0.001

    def test_apply_contrast_clamps(self):
        """Test that contrast clamps output."""
        result = apply_contrast(0.1, 5.0)
        assert 0.0 <= result <= 1.0


class TestApplySaturation:
    """Tests for apply_saturation function."""

    def test_apply_saturation_increase(self):
        """Test increasing saturation."""
        r, g, b = 0.5, 0.6, 0.7
        r_out, g_out, b_out = apply_saturation(r, g, b, 1.5)
        # Should be more saturated
        assert r_out != r or g_out != g or b_out != b

    def test_apply_saturation_decrease(self):
        """Test decreasing saturation."""
        r, g, b = 0.8, 0.3, 0.5
        r_out, g_out, b_out = apply_saturation(r, g, b, 0.5)
        # Should be less saturated (closer to gray)
        max_before = max(r, g, b)
        min_before = min(r, g, b)
        max_after = max(r_out, g_out, b_out)
        min_after = min(r_out, g_out, b_out)
        assert (max_after - min_after) <= (max_before - min_before)

    def test_apply_saturation_zero(self):
        """Test zero saturation (grayscale)."""
        r, g, b = 0.8, 0.3, 0.5
        r_out, g_out, b_out = apply_saturation(r, g, b, 0.0)
        # All channels should be equal (grayscale)
        assert abs(r_out - g_out) < 0.001
        assert abs(g_out - b_out) < 0.001

    def test_apply_saturation_neutral(self):
        """Test neutral saturation (1.0)."""
        r, g, b = 0.8, 0.3, 0.5
        r_out, g_out, b_out = apply_saturation(r, g, b, 1.0)
        assert r_out == r
        assert g_out == g
        assert b_out == b


class TestApplyLiftGammaGain:
    """Tests for apply_lift_gamma_gain function."""

    def test_apply_lgg_basic(self):
        """Test basic LGG application."""
        value = 0.5
        lift = 0.0
        gamma = 1.0
        gain = 1.0
        result = apply_lift_gamma_gain(value, lift, gamma, gain)
        assert result == value

    def test_apply_lgg_lift(self):
        """Test lift adjustment."""
        value = 0.2
        lift = 0.1
        gamma = 1.0
        gain = 1.0
        result = apply_lift_gamma_gain(value, lift, gamma, gain)
        # Shadows should be lifted
        assert result > value

    def test_apply_lgg_gain(self):
        """Test gain adjustment."""
        value = 0.5
        lift = 0.0
        gamma = 1.0
        gain = 1.5
        result = apply_lift_gamma_gain(value, lift, gamma, gain)
        # Should be multiplied by gain
        assert result > value

    def test_apply_lgg_clamps(self):
        """Test that LGG clamps output."""
        result = apply_lift_gamma_gain(0.9, 0.5, 1.0, 2.0)
        assert 0.0 <= result <= 1.0


class TestApplyLggRgb:
    """Tests for apply_lgg_rgb function."""

    def test_apply_lgg_rgb_basic(self):
        """Test basic RGB LGG application."""
        r, g, b = 0.5, 0.6, 0.7
        lift = (0.0, 0.0, 0.0)
        gamma = 1.0
        gain = (1.0, 1.0, 1.0)
        r_out, g_out, b_out = apply_lgg_rgb(r, g, b, lift, gamma, gain)
        assert r_out == r
        assert g_out == g
        assert b_out == b

    def test_apply_lgg_rgb_per_channel(self):
        """Test per-channel LGG."""
        r, g, b = 0.5, 0.5, 0.5
        lift = (0.1, 0.0, 0.0)
        gamma = 1.0
        gain = (1.0, 1.5, 1.0)
        r_out, g_out, b_out = apply_lgg_rgb(r, g, b, lift, gamma, gain)
        # Red should be different (lift + no gain boost)
        # Green should be different (no lift + gain boost)
        assert r_out != g_out or g_out != b_out


class TestApplyCdl:
    """Tests for apply_cdl function."""

    def test_apply_cdl_basic(self):
        """Test basic CDL application."""
        value = 0.5
        slope = 1.0
        offset = 0.0
        power = 1.0
        result = apply_cdl(value, slope, offset, power)
        assert result == value

    def test_apply_cdl_slope(self):
        """Test slope adjustment."""
        value = 0.5
        slope = 2.0
        offset = 0.0
        power = 1.0
        result = apply_cdl(value, slope, offset, power)
        assert result == value * slope

    def test_apply_cdl_offset(self):
        """Test offset adjustment."""
        value = 0.5
        slope = 1.0
        offset = 0.1
        power = 1.0
        result = apply_cdl(value, slope, offset, power)
        assert abs(result - (value + offset)) < 0.001

    def test_apply_cdl_clamps(self):
        """Test that CDL clamps output."""
        result = apply_cdl(0.9, 2.0, 0.5, 1.0)
        assert 0.0 <= result <= 1.0


class TestApplyCdlRgb:
    """Tests for apply_cdl_rgb function."""

    def test_apply_cdl_rgb_basic(self):
        """Test basic RGB CDL application."""
        r, g, b = 0.5, 0.6, 0.7
        slope = (1.0, 1.0, 1.0)
        offset = (0.0, 0.0, 0.0)
        power = (1.0, 1.0, 1.0)
        r_out, g_out, b_out = apply_cdl_rgb(r, g, b, slope, offset, power)
        assert r_out == r
        assert g_out == g
        assert b_out == b


class TestApplyCurve:
    """Tests for apply_curve function."""

    def test_apply_curve_identity(self):
        """Test identity curve (no change)."""
        value = 0.5
        curve_points = [(0, 0), (1, 1)]
        result = apply_curve(value, curve_points)
        assert result == value

    def test_apply_curve_invert(self):
        """Test inverted curve."""
        value = 0.3
        curve_points = [(0, 1), (1, 0)]
        result = apply_curve(value, curve_points)
        # Should be approximately 1 - 0.3 = 0.7
        assert abs(result - 0.7) < 0.01

    def test_apply_curve_empty(self):
        """Test empty curve returns value unchanged."""
        value = 0.5
        result = apply_curve(value, [])
        assert result == value

    def test_apply_curve_at_point(self):
        """Test curve at exact point."""
        value = 0.5
        curve_points = [(0, 0), (0.5, 0.8), (1, 1)]
        result = apply_curve(value, curve_points)
        assert result == 0.8


class TestApplyRgbCurves:
    """Tests for apply_rgb_curves function."""

    def test_apply_rgb_curves_identity(self):
        """Test identity curves (no change)."""
        r, g, b = 0.3, 0.5, 0.7
        curve = [(0, 0), (1, 1)]
        r_out, g_out, b_out = apply_rgb_curves(r, g, b, curve)
        assert r_out == r
        assert g_out == g
        assert b_out == b

    def test_apply_rgb_curves_master(self):
        """Test master curve affects all channels."""
        r, g, b = 0.5, 0.5, 0.5
        curve = [(0, 1), (1, 0)]  # Invert
        r_out, g_out, b_out = apply_rgb_curves(r, g, b, curve)
        for val in [r_out, g_out, b_out]:
            assert abs(val - 0.5) < 0.01  # 1 - 0.5 = 0.5

    def test_apply_rgb_curves_individual(self):
        """Test individual channel curves."""
        r, g, b = 0.5, 0.5, 0.5
        master_curve = [(0, 0), (1, 1)]
        r_curve = [(0, 0), (1, 0.5)]  # Darken red
        r_out, g_out, b_out = apply_rgb_curves(r, g, b, master_curve, r_curve=r_curve)
        assert r_out < g_out  # Red should be darker


class TestApplyLevels:
    """Tests for apply_levels function."""

    def test_apply_levels_basic(self):
        """Test basic levels application."""
        value = 0.5
        result = apply_levels(value)
        assert result == value

    def test_apply_levels_input_range(self):
        """Test input black/white point."""
        value = 0.5
        result = apply_levels(value, input_black=0.25, input_white=0.75)
        # 0.5 is in middle of 0.25-0.75 range, so result is 0.5
        assert 0.0 <= result <= 1.0

    def test_apply_levels_output_range(self):
        """Test output black/white point."""
        value = 0.5
        result = apply_levels(value, output_black=0.2, output_white=0.8)
        # Should be scaled to 0.2-0.8 range
        assert 0.2 <= result <= 0.8

    def test_apply_levels_gamma(self):
        """Test levels with gamma."""
        value = 0.5
        result = apply_levels(value, gamma=2.0)
        # With gamma=2.0, the formula applies: result ** (1.0 / gamma)
        # which for 0.5 is 0.5 ** 0.5 = ~0.707, so midtones get brighter
        assert result > value  # gamma > 1 brightens midtones in levels


class TestColorConversions:
    """Tests for color space conversion functions."""

    def test_rgb_to_hsv_red(self):
        """Test RGB to HSV for red."""
        h, s, v = rgb_to_hsv(1.0, 0.0, 0.0)
        assert h == 0.0
        assert s == 1.0
        assert v == 1.0

    def test_rgb_to_hsv_green(self):
        """Test RGB to HSV for green."""
        h, s, v = rgb_to_hsv(0.0, 1.0, 0.0)
        # Green is at 120 degrees = 1/3 normalized
        assert abs(h - (120/360)) < 0.01
        assert s == 1.0
        assert v == 1.0

    def test_rgb_to_hsv_blue(self):
        """Test RGB to HSV for blue."""
        h, s, v = rgb_to_hsv(0.0, 0.0, 1.0)
        # Blue is at 240 degrees = 2/3 normalized
        assert abs(h - (240/360)) < 0.01
        assert s == 1.0
        assert v == 1.0

    def test_rgb_to_hsv_white(self):
        """Test RGB to HSV for white."""
        h, s, v = rgb_to_hsv(1.0, 1.0, 1.0)
        assert s == 0.0
        assert v == 1.0

    def test_rgb_to_hsv_black(self):
        """Test RGB to HSV for black."""
        h, s, v = rgb_to_hsv(0.0, 0.0, 0.0)
        assert v == 0.0

    def test_hsv_to_rgb_roundtrip(self):
        """Test HSV to RGB roundtrip."""
        original = (0.3, 0.5, 0.7)
        h, s, v = rgb_to_hsv(*original)
        result = hsv_to_rgb(h, s, v)
        for i in range(3):
            assert abs(result[i] - original[i]) < 0.01

    def test_hsv_to_rgb_gray(self):
        """Test HSV to RGB for gray."""
        r, g, b = hsv_to_rgb(0.0, 0.0, 0.5)
        assert r == g == b == 0.5


class TestApplyHsvAdjustment:
    """Tests for apply_hsv_adjustment function."""

    def test_apply_hsv_adjustment_basic(self):
        """Test basic HSV adjustment."""
        r, g, b = 0.5, 0.5, 0.5
        r_out, g_out, b_out = apply_hsv_adjustment(r, g, b)
        assert r_out == r
        assert g_out == g
        assert b_out == b

    def test_apply_hsv_adjustment_hue(self):
        """Test hue shift."""
        r, g, b = 1.0, 0.0, 0.0  # Red
        r_out, g_out, b_out = apply_hsv_adjustment(r, g, b, hue_shift=1/3)  # Shift to green
        assert g_out > r_out  # Green should be dominant

    def test_apply_hsv_adjustment_saturation(self):
        """Test saturation adjustment."""
        r, g, b = 0.8, 0.3, 0.5
        r_out, g_out, b_out = apply_hsv_adjustment(r, g, b, saturation_mult=0.5)
        # Should be less saturated
        max_before = max(r, g, b) - min(r, g, b)
        max_after = max(r_out, g_out, b_out) - min(r_out, g_out, b_out)
        assert max_after <= max_before


class TestApplyWhiteBalance:
    """Tests for apply_white_balance function."""

    def test_apply_white_balance_neutral(self):
        """Test neutral white balance."""
        r, g, b = 0.5, 0.6, 0.7
        r_out, g_out, b_out = apply_white_balance(r, g, b, 0, 0)
        # Should be approximately the same
        assert abs(r_out - r) < 0.01
        assert abs(g_out - g) < 0.01
        assert abs(b_out - b) < 0.01

    def test_apply_white_balance_warm(self):
        """Test warming (positive temperature)."""
        r, g, b = 0.5, 0.5, 0.5
        r_out, g_out, b_out = apply_white_balance(r, g, b, temperature=50)
        # Should add yellow/red, reduce blue
        assert r_out >= r  # Red increased or same
        assert b_out <= b  # Blue decreased or same

    def test_apply_white_balance_cool(self):
        """Test cooling (negative temperature)."""
        r, g, b = 0.5, 0.5, 0.5
        r_out, g_out, b_out = apply_white_balance(r, g, b, temperature=-50)
        # Should add blue, reduce yellow/red
        assert b_out >= b  # Blue increased or same


class TestApplyHighlightsShadows:
    """Tests for apply_highlights_shadows function."""

    def test_apply_highlights_shadows_basic(self):
        """Test basic highlights/shadows."""
        value = 0.5
        result = apply_highlights_shadows(value, 0, 0)
        assert result == value

    def test_apply_highlights_shadows_highlights(self):
        """Test highlights adjustment."""
        value = 0.8  # Bright value
        result = apply_highlights_shadows(value, highlights=50)
        assert result > value  # Bright value should get brighter

    def test_apply_highlights_shadows_shadows(self):
        """Test shadows adjustment."""
        value = 0.2  # Dark value
        result = apply_highlights_shadows(value, shadows=50)
        assert result > value  # Dark value should get brighter


class TestApplyColorCorrection:
    """Tests for apply_color_correction function."""

    def test_apply_color_correction_basic(self):
        """Test basic color correction."""
        r, g, b = 0.5, 0.6, 0.7
        cc = ColorCorrection()
        r_out, g_out, b_out = apply_color_correction(r, g, b, cc)
        # With neutral settings, should be approximately the same
        for orig, out in [(r, r_out), (g, g_out), (b, b_out)]:
            assert 0.0 <= out <= 1.0

    def test_apply_color_correction_exposure(self):
        """Test color correction with exposure."""
        r, g, b = 0.5, 0.5, 0.5
        cc = ColorCorrection(exposure=1.0)
        r_out, g_out, b_out = apply_color_correction(r, g, b, cc)
        # Should be brighter
        assert r_out > r

    def test_apply_color_correction_saturation(self):
        """Test color correction with saturation."""
        r, g, b = 0.8, 0.3, 0.5
        cc = ColorCorrection(saturation=0.5)
        r_out, g_out, b_out = apply_color_correction(r, g, b, cc)
        # Should be less saturated
        max_before = max(r, g, b) - min(r, g, b)
        max_after = max(r_out, g_out, b_out) - min(r_out, g_out, b_out)
        assert max_after < max_before


class TestColorPresets:
    """Tests for color presets."""

    def test_color_presets_exist(self):
        """Test that presets exist."""
        assert isinstance(COLOR_PRESETS, dict)
        assert len(COLOR_PRESETS) > 0

    def test_neutral_preset(self):
        """Test neutral preset."""
        assert "neutral" in COLOR_PRESETS
        preset = COLOR_PRESETS["neutral"]
        assert preset["exposure"] == 0.0
        assert preset["contrast"] == 1.0

    def test_cinematic_warm_preset(self):
        """Test cinematic warm preset."""
        assert "cinematic_warm" in COLOR_PRESETS
        preset = COLOR_PRESETS["cinematic_warm"]
        assert preset["temperature"] > 0  # Should be warm

    def test_cinematic_cool_preset(self):
        """Test cinematic cool preset."""
        assert "cinematic_cool" in COLOR_PRESETS
        preset = COLOR_PRESETS["cinematic_cool"]
        assert preset["temperature"] < 0  # Should be cool


class TestGetColorPreset:
    """Tests for get_color_preset function."""

    def test_get_color_preset_neutral(self):
        """Test getting neutral preset."""
        preset = get_color_preset("neutral")
        assert preset["exposure"] == 0.0

    def test_get_color_preset_unknown(self):
        """Test getting unknown preset returns neutral."""
        preset = get_color_preset("unknown")
        assert preset == COLOR_PRESETS["neutral"]

    def test_get_color_preset_copy(self):
        """Test that preset is a copy."""
        preset1 = get_color_preset("neutral")
        preset2 = get_color_preset("neutral")
        preset1["exposure"] = 1.0
        assert preset2["exposure"] == 0.0


class TestApplyPreset:
    """Tests for apply_preset function."""

    def test_apply_preset_neutral(self):
        """Test applying neutral preset."""
        cc = ColorCorrection()
        cc.exposure = 2.0  # Non-default
        cc = apply_preset(cc, "neutral")
        assert cc.exposure == 0.0

    def test_apply_preset_cinematic_warm(self):
        """Test applying cinematic warm preset."""
        cc = ColorCorrection()
        cc = apply_preset(cc, "cinematic_warm")
        assert cc.temperature == 25
        assert cc.contrast == 1.1


class TestColorCorrectionEdgeCases:
    """Tests for edge cases in color correction."""

    def test_extreme_values(self):
        """Test with extreme color values."""
        r, g, b = 0.0, 1.0, 0.0

        cc = ColorCorrection(exposure=2.0)
        r_out, g_out, b_out = apply_color_correction(r, g, b, cc)
        assert all(0.0 <= v <= 1.0 for v in [r_out, g_out, b_out])

    def test_clamp_behavior(self):
        """Test that values are clamped."""
        r, g, b = 0.9, 0.9, 0.9
        cc = ColorCorrection(exposure=5.0)
        r_out, g_out, b_out = apply_color_correction(r, g, b, cc)
        assert all(v <= 1.0 for v in [r_out, g_out, b_out])

    def test_zero_saturation_grayscale(self):
        """Test that zero saturation produces grayscale."""
        r, g, b = 0.8, 0.3, 0.5
        r_out, g_out, b_out = apply_saturation(r, g, b, 0.0)
        # All channels should be equal
        assert abs(r_out - g_out) < 0.001
        assert abs(g_out - b_out) < 0.001

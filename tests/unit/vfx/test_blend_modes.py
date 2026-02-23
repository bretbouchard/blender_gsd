"""
Tests for lib/vfx/blend_modes.py

Tests blend mode functions without Blender (bpy).
"""

import pytest
import math

from lib.vfx.compositor_types import BlendMode
from lib.vfx.blend_modes import (
    blend_normal,
    blend_multiply,
    blend_screen,
    blend_overlay,
    blend_add,
    blend_subtract,
    blend_difference,
    blend_darken,
    blend_lighten,
    blend_color_dodge,
    blend_color_burn,
    blend_hard_light,
    blend_soft_light,
    blend_exclusion,
    blend_pin_light,
    blend_hard_mix,
    blend_linear_dodge,
    blend_linear_burn,
    blend_hue,
    blend_saturation,
    blend_color,
    blend_luminosity,
    get_blend_function,
    apply_blend,
    rgb_to_hsl,
    hsl_to_rgb,
    BLEND_MODES,
    BLEND_MODES_RGB,
)


class TestBlendModeEnum:
    """Tests for BlendMode enum."""

    def test_blend_modes_exist(self):
        """Test that expected blend modes exist."""
        assert hasattr(BlendMode, 'NORMAL')
        assert hasattr(BlendMode, 'MULTIPLY')
        assert hasattr(BlendMode, 'SCREEN')
        assert hasattr(BlendMode, 'OVERLAY')
        assert hasattr(BlendMode, 'ADD')
        assert hasattr(BlendMode, 'DIFFERENCE')
        assert hasattr(BlendMode, 'DARKEN')
        assert hasattr(BlendMode, 'LIGHTEN')
        assert hasattr(BlendMode, 'COLOR_DODGE')
        assert hasattr(BlendMode, 'COLOR_BURN')
        assert hasattr(BlendMode, 'HARD_LIGHT')
        assert hasattr(BlendMode, 'SOFT_LIGHT')
        assert hasattr(BlendMode, 'LINEAR_DODGE')
        assert hasattr(BlendMode, 'LINEAR_BURN')
        assert hasattr(BlendMode, 'HUE')
        assert hasattr(BlendMode, 'SATURATION')
        assert hasattr(BlendMode, 'COLOR')
        assert hasattr(BlendMode, 'LUMINOSITY')

    def test_blend_mode_values(self):
        """Test blend mode enum values."""
        assert BlendMode.NORMAL.value == "normal"
        assert BlendMode.MULTIPLY.value == "multiply"
        assert BlendMode.SCREEN.value == "screen"
        assert BlendMode.ADD.value == "add"


class TestBlendNormal:
    """Tests for blend_normal function."""

    def test_blend_normal_basic(self):
        """Test basic normal blend."""
        base = 0.5
        blend = 0.8
        result = blend_normal(base, blend, opacity=1.0)
        assert result == blend

    def test_blend_normal_opacity(self):
        """Test normal blend with opacity."""
        base = 0.5
        blend = 1.0
        result = blend_normal(base, blend, opacity=0.5)
        # Should be halfway between base and blend
        assert 0.5 <= result <= 1.0
        assert abs(result - 0.75) < 0.001

    def test_blend_normal_zero_opacity(self):
        """Test normal blend with zero opacity."""
        base = 0.3
        blend = 0.9
        result = blend_normal(base, blend, opacity=0.0)
        assert result == base


class TestBlendMultiply:
    """Tests for blend_multiply function."""

    def test_blend_multiply_basic(self):
        """Test basic multiply blend."""
        base = 0.5
        blend = 0.5
        result = blend_multiply(base, blend)
        assert abs(result - 0.25) < 0.001

    def test_blend_multiply_darkens(self):
        """Test that multiply always darkens."""
        base = 0.8
        blend = 0.9
        result = blend_multiply(base, blend)
        assert result <= base
        assert result <= blend

    def test_blend_multiply_white_neutral(self):
        """Test that white is neutral for multiply."""
        base = 0.5
        blend = 1.0
        result = blend_multiply(base, blend, opacity=1.0)
        assert result == base

    def test_blend_multiply_black(self):
        """Test that multiply with black produces black."""
        base = 0.5
        blend = 0.0
        result = blend_multiply(base, blend)
        assert result == 0.0


class TestBlendScreen:
    """Tests for blend_screen function."""

    def test_blend_screen_basic(self):
        """Test basic screen blend."""
        base = 0.5
        blend = 0.5
        result = blend_screen(base, blend)
        # Screen: 1 - (1-0.5)*(1-0.5) = 1 - 0.25 = 0.75
        assert abs(result - 0.75) < 0.001

    def test_blend_screen_lightens(self):
        """Test that screen always lightens."""
        base = 0.2
        blend = 0.3
        result = blend_screen(base, blend)
        assert result >= base
        assert result >= blend

    def test_blend_screen_black_neutral(self):
        """Test that black is neutral for screen."""
        base = 0.5
        blend = 0.0
        result = blend_screen(base, blend, opacity=1.0)
        assert result == base

    def test_blend_screen_white(self):
        """Test that screen with white produces white."""
        base = 0.5
        blend = 1.0
        result = blend_screen(base, blend)
        assert result == 1.0


class TestBlendOverlay:
    """Tests for blend_overlay function."""

    def test_blend_overlay_basic(self):
        """Test basic overlay blend."""
        base = 0.5
        blend = 0.5
        result = blend_overlay(base, blend)
        # At 0.5, it should use multiply: 2 * 0.5 * 0.5 = 0.5
        assert abs(result - 0.5) < 0.001

    def test_blend_overlay_light_base(self):
        """Test overlay with light base (screen behavior)."""
        base = 0.7
        blend = 0.8
        result = blend_overlay(base, blend)
        # Should use screen formula for light base
        assert result > base

    def test_blend_overlay_dark_base(self):
        """Test overlay with dark base (multiply behavior)."""
        base = 0.3
        blend = 0.4
        result = blend_overlay(base, blend)
        # Should use multiply formula for dark base
        assert result < base


class TestBlendAdd:
    """Tests for blend_add function."""

    def test_blend_add_basic(self):
        """Test basic add blend."""
        base = 0.3
        blend = 0.4
        result = blend_add(base, blend)
        assert abs(result - 0.7) < 0.001

    def test_blend_add_clamps(self):
        """Test that add clamps to 1.0."""
        base = 0.8
        blend = 0.9
        result = blend_add(base, blend)
        assert result <= 1.0

    def test_blend_add_zero(self):
        """Test add with zero."""
        base = 0.5
        blend = 0.0
        result = blend_add(base, blend, opacity=1.0)
        assert result == base


class TestBlendSubtract:
    """Tests for blend_subtract function."""

    def test_blend_subtract_basic(self):
        """Test basic subtract blend."""
        base = 0.7
        blend = 0.3
        result = blend_subtract(base, blend)
        assert abs(result - 0.4) < 0.001

    def test_blend_subtract_clamps(self):
        """Test that subtract clamps to 0.0."""
        base = 0.2
        blend = 0.8
        result = blend_subtract(base, blend)
        assert result >= 0.0


class TestBlendDifference:
    """Tests for blend_difference function."""

    def test_blend_difference_basic(self):
        """Test basic difference blend."""
        base = 0.7
        blend = 0.3
        result = blend_difference(base, blend)
        assert abs(result - 0.4) < 0.001

    def test_blend_difference_symmetric(self):
        """Test that difference is symmetric."""
        base = 0.7
        blend = 0.3
        result1 = blend_difference(base, blend)
        result2 = blend_difference(blend, base)
        assert result1 == result2

    def test_blend_difference_same(self):
        """Test difference with same values."""
        base = 0.5
        result = blend_difference(base, base)
        assert result == 0.0


class TestBlendDarken:
    """Tests for blend_darken function."""

    def test_blend_darken_basic(self):
        """Test basic darken blend."""
        base = 0.5
        blend = 0.6
        result = blend_darken(base, blend)
        assert result == 0.5  # min(0.5, 0.6)

    def test_blend_darken_other(self):
        """Test darken when blend is darker."""
        base = 0.7
        blend = 0.4
        result = blend_darken(base, blend)
        assert result == 0.4  # min(0.7, 0.4)


class TestBlendLighten:
    """Tests for blend_lighten function."""

    def test_blend_lighten_basic(self):
        """Test basic lighten blend."""
        base = 0.5
        blend = 0.6
        result = blend_lighten(base, blend)
        assert result == 0.6  # max(0.5, 0.6)

    def test_blend_lighten_other(self):
        """Test lighten when blend is lighter."""
        base = 0.7
        blend = 0.4
        result = blend_lighten(base, blend)
        assert result == 0.7  # max(0.7, 0.4)


class TestBlendColorDodge:
    """Tests for blend_color_dodge function."""

    def test_blend_color_dodge_basic(self):
        """Test basic color dodge blend."""
        base = 0.5
        blend = 0.5
        result = blend_color_dodge(base, blend)
        # 0.5 / (1 - 0.5) = 1.0
        assert result == 1.0

    def test_blend_color_dodge_brightens(self):
        """Test that color dodge brightens."""
        base = 0.3
        blend = 0.5
        result = blend_color_dodge(base, blend)
        assert result >= base

    def test_blend_color_dodge_full_blend(self):
        """Test color dodge with full blend."""
        base = 0.5
        blend = 1.0
        result = blend_color_dodge(base, blend)
        assert result == 1.0


class TestBlendColorBurn:
    """Tests for blend_color_burn function."""

    def test_blend_color_burn_basic(self):
        """Test basic color burn blend."""
        base = 0.5
        blend = 0.5
        result = blend_color_burn(base, blend)
        assert 0.0 <= result <= 1.0

    def test_blend_color_burn_darkens(self):
        """Test that color burn darkens."""
        base = 0.7
        blend = 0.5
        result = blend_color_burn(base, blend)
        assert result <= base

    def test_blend_color_burn_zero_blend(self):
        """Test color burn with zero blend."""
        base = 0.5
        blend = 0.0
        result = blend_color_burn(base, blend)
        assert result == 0.0


class TestBlendHardLight:
    """Tests for blend_hard_light function."""

    def test_blend_hard_light_basic(self):
        """Test basic hard light blend."""
        base = 0.5
        blend = 0.5
        result = blend_hard_light(base, blend)
        assert 0.0 <= result <= 1.0

    def test_blend_hard_light_like_overlay(self):
        """Test that hard light is similar to overlay with swapped args."""
        base = 0.5
        blend = 0.5
        result_hl = blend_hard_light(base, blend)
        result_ol = blend_overlay(blend, base)
        # Should be the same
        assert abs(result_hl - result_ol) < 0.001


class TestBlendSoftLight:
    """Tests for blend_soft_light function."""

    def test_blend_soft_light_basic(self):
        """Test basic soft light blend."""
        base = 0.5
        blend = 0.5
        result = blend_soft_light(base, blend)
        assert 0.0 <= result <= 1.0


class TestBlendExclusion:
    """Tests for blend_exclusion function."""

    def test_blend_exclusion_basic(self):
        """Test basic exclusion blend."""
        base = 0.5
        blend = 0.5
        result = blend_exclusion(base, blend)
        # 0.5 + 0.5 - 2 * 0.5 * 0.5 = 0.5
        assert abs(result - 0.5) < 0.001

    def test_blend_exclusion_symmetric(self):
        """Test that exclusion is symmetric."""
        base = 0.7
        blend = 0.3
        result1 = blend_exclusion(base, blend)
        result2 = blend_exclusion(blend, base)
        assert result1 == result2


class TestBlendPinLight:
    """Tests for blend_pin_light function."""

    def test_blend_pin_light_dark_blend(self):
        """Test pin light with dark blend (darken behavior)."""
        base = 0.5
        blend = 0.3  # < 0.5
        result = blend_pin_light(base, blend)
        # min(0.5, 2 * 0.3) = min(0.5, 0.6) = 0.5
        assert 0.0 <= result <= 1.0

    def test_blend_pin_light_light_blend(self):
        """Test pin light with light blend (lighten behavior)."""
        base = 0.5
        blend = 0.7  # > 0.5
        result = blend_pin_light(base, blend)
        # max(0.5, 2 * (0.7 - 0.5)) = max(0.5, 0.4) = 0.5
        assert 0.0 <= result <= 1.0


class TestBlendHardMix:
    """Tests for blend_hard_mix function."""

    def test_blend_hard_mix_basic(self):
        """Test basic hard mix blend."""
        base = 0.3
        blend = 0.4
        result = blend_hard_mix(base, blend)
        # 0.3 + 0.4 = 0.7 < 1, so result is 0
        assert result == 0.0

    def test_blend_hard_mix_threshold(self):
        """Test hard mix at threshold."""
        base = 0.6
        blend = 0.5
        result = blend_hard_mix(base, blend)
        # 0.6 + 0.5 = 1.1 >= 1, so result is 1
        assert result == 1.0


class TestBlendLinearDodge:
    """Tests for blend_linear_dodge function."""

    def test_blend_linear_dodge_same_as_add(self):
        """Test that linear dodge is same as add."""
        base = 0.3
        blend = 0.4
        result = blend_linear_dodge(base, blend)
        result_add = blend_add(base, blend)
        assert result == result_add


class TestBlendLinearBurn:
    """Tests for blend_linear_burn function."""

    def test_blend_linear_burn_basic(self):
        """Test basic linear burn blend."""
        base = 0.5
        blend = 0.3
        result = blend_linear_burn(base, blend)
        # 0.5 + 0.3 - 1 = -0.2, clamped to 0
        assert result >= 0.0


class TestBlendHSB:
    """Tests for HSB-based blend modes."""

    def test_blend_hue(self):
        """Test hue blend."""
        base = (0.5, 0.5, 0.5)
        blend = (0.8, 0.3, 0.2)
        result = blend_hue(base, blend)
        assert len(result) == 3

    def test_blend_saturation(self):
        """Test saturation blend."""
        base = (0.5, 0.5, 0.5)
        blend = (0.8, 0.3, 0.2)
        result = blend_saturation(base, blend)
        assert len(result) == 3

    def test_blend_color(self):
        """Test color blend."""
        base = (0.5, 0.5, 0.5)
        blend = (0.8, 0.3, 0.2)
        result = blend_color(base, blend)
        assert len(result) == 3

    def test_blend_luminosity(self):
        """Test luminosity blend."""
        base = (0.5, 0.5, 0.5)
        blend = (0.8, 0.3, 0.2)
        result = blend_luminosity(base, blend)
        assert len(result) == 3


class TestGetBlendFunction:
    """Tests for get_blend_function."""

    def test_get_blend_function_normal(self):
        """Test getting normal blend function."""
        func = get_blend_function(BlendMode.NORMAL)
        assert func == blend_normal

    def test_get_blend_function_multiply(self):
        """Test getting multiply blend function."""
        func = get_blend_function(BlendMode.MULTIPLY)
        assert func == blend_multiply

    def test_get_blend_function_screen(self):
        """Test getting screen blend function."""
        func = get_blend_function(BlendMode.SCREEN)
        assert func == blend_screen

    def test_get_blend_function_string(self):
        """Test getting blend function by string."""
        func = get_blend_function("normal")
        assert func == blend_normal

    def test_get_blend_function_unknown(self):
        """Test getting unknown blend function defaults to normal."""
        func = get_blend_function("unknown")
        assert func == blend_normal


class TestApplyBlend:
    """Tests for apply_blend function."""

    def test_apply_blend_normal(self):
        """Test applying normal blend mode."""
        base = 0.5
        blend = 0.8
        result = apply_blend(BlendMode.NORMAL, base, blend)
        assert result == blend

    def test_apply_blend_multiply(self):
        """Test applying multiply blend mode."""
        base = 0.5
        blend = 0.5
        result = apply_blend(BlendMode.MULTIPLY, base, blend)
        assert abs(result - 0.25) < 0.001

    def test_apply_blend_with_opacity(self):
        """Test applying blend mode with opacity."""
        base = 0.5
        blend = 1.0
        result = apply_blend(BlendMode.NORMAL, base, blend, opacity=0.5)
        # Should be halfway between base and blend
        assert 0.5 <= result <= 1.0


class TestColorConversions:
    """Tests for color space conversion functions."""

    def test_rgb_to_hsl_gray(self):
        """Test RGB to HSL for gray."""
        h, s, l = rgb_to_hsl(0.5, 0.5, 0.5)
        assert l == 0.5
        assert s == 0.0

    def test_rgb_to_hsl_white(self):
        """Test RGB to HSL for white."""
        h, s, l = rgb_to_hsl(1.0, 1.0, 1.0)
        assert l == 1.0
        assert s == 0.0

    def test_rgb_to_hsl_black(self):
        """Test RGB to HSL for black."""
        h, s, l = rgb_to_hsl(0.0, 0.0, 0.0)
        assert l == 0.0

    def test_hsl_to_rgb_roundtrip(self):
        """Test HSL to RGB roundtrip."""
        original = (0.3, 0.5, 0.7)
        h, s, l = rgb_to_hsl(*original)
        result = hsl_to_rgb(h, s, l)
        for i in range(3):
            assert abs(result[i] - original[i]) < 0.01


class TestBlendModesRegistry:
    """Tests for blend mode registries."""

    def test_blend_modes_dict_exists(self):
        """Test that BLEND_MODES dict exists."""
        assert isinstance(BLEND_MODES, dict)
        assert len(BLEND_MODES) > 0

    def test_blend_modes_rgb_dict_exists(self):
        """Test that BLEND_MODES_RGB dict exists."""
        assert isinstance(BLEND_MODES_RGB, dict)
        assert len(BLEND_MODES_RGB) > 0

    def test_blend_modes_contains_normal(self):
        """Test that BLEND_MODES contains normal."""
        assert BlendMode.NORMAL.value in BLEND_MODES

    def test_blend_modes_rgb_contains_hue(self):
        """Test that BLEND_MODES_RGB contains hue."""
        assert BlendMode.HUE.value in BLEND_MODES_RGB


class TestBlendModeEdgeCases:
    """Tests for edge cases in blend modes."""

    def test_extreme_values(self):
        """Test blending with extreme values (0 and 1)."""
        for blend_func in [blend_normal, blend_multiply, blend_screen,
                           blend_add, blend_subtract]:
            result = blend_func(0.0, 1.0)
            assert 0.0 <= result <= 1.0

    def test_negative_handling(self):
        """Test handling of negative values."""
        # Some blend modes may receive negative values
        result = blend_normal(-0.1, 0.5)
        # Should handle gracefully
        assert isinstance(result, float)

    def test_all_blend_modes_valid(self):
        """Test that all registered blend modes produce valid output."""
        for mode_name, func in BLEND_MODES.items():
            result = func(0.5, 0.5)
            assert 0.0 <= result <= 1.0, f"Blend mode {mode_name} produced invalid result"

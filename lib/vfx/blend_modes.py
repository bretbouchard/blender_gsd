"""
Blend Modes

Standard blend mode implementations for compositing.

These are mathematical implementations. For actual pixel processing,
use with numpy arrays or integrate with Blender's compositor.

Part of Phase 12.1: Compositor (REQ-COMP-02)
"""

from __future__ import annotations
from typing import Tuple, Union, Callable
import math

# Type alias for image data (would be numpy array in practice)
ImageLike = Union[list, tuple, any]

from .compositor_types import BlendMode


def _clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clamp a value to a range."""
    return max(min_val, min(max_val, value))


def _apply_opacity(base: float, over: float, opacity: float) -> float:
    """Apply opacity blending."""
    return base * (1 - opacity) + over * opacity


# ==================== Basic Blend Modes ====================

def blend_normal(base: float, over: float, opacity: float = 1.0) -> float:
    """
    Normal blend mode (alpha blending).
    Result = Over * Opacity + Base * (1 - Opacity)
    """
    return _apply_opacity(base, over, opacity)


def blend_multiply(base: float, over: float, opacity: float = 1.0) -> float:
    """
    Multiply blend mode.
    Result = Base * Over
    Darkens the image.
    """
    result = base * over
    return _apply_opacity(base, result, opacity)


def blend_screen(base: float, over: float, opacity: float = 1.0) -> float:
    """
    Screen blend mode.
    Result = 1 - (1 - Base) * (1 - Over)
    Lightens the image.
    """
    result = 1 - (1 - base) * (1 - over)
    return _apply_opacity(base, result, opacity)


def blend_add(base: float, over: float, opacity: float = 1.0) -> float:
    """
    Additive blend (Linear Dodge).
    Result = Base + Over
    """
    result = _clamp(base + over)
    return _apply_opacity(base, result, opacity)


def blend_subtract(base: float, over: float, opacity: float = 1.0) -> float:
    """
    Subtract blend mode.
    Result = Base - Over
    """
    result = _clamp(base - over)
    return _apply_opacity(base, result, opacity)


def blend_difference(base: float, over: float, opacity: float = 1.0) -> float:
    """
    Difference blend mode.
    Result = |Base - Over|
    """
    result = abs(base - over)
    return _apply_opacity(base, result, opacity)


# ==================== Contrast Blend Modes ====================

def blend_overlay(base: float, over: float, opacity: float = 1.0) -> float:
    """
    Overlay blend mode.
    Combines multiply and screen based on base value.
    """
    if base < 0.5:
        result = 2 * base * over
    else:
        result = 1 - 2 * (1 - base) * (1 - over)
    return _apply_opacity(base, result, opacity)


def blend_soft_light(base: float, over: float, opacity: float = 1.0) -> float:
    """
    Soft light blend mode.
    Softer version of overlay.
    """
    if over < 0.5:
        result = base - (1 - 2 * over) * base * (1 - base)
    else:
        d = _clamp(2 * over - 1)
        if base < 0.25:
            result = base + d * ((16 * base - 12) * base + 3) * base
        else:
            result = base + d * (math.sqrt(base) - base)
    return _apply_opacity(base, result, opacity)


def blend_hard_light(base: float, over: float, opacity: float = 1.0) -> float:
    """
    Hard light blend mode.
    Same as overlay but swaps base and over.
    """
    # Hard light is overlay with swapped operands
    return blend_overlay(over, base, opacity)


# ==================== Dodge/Burn Blend Modes ====================

def blend_color_dodge(base: float, over: float, opacity: float = 1.0) -> float:
    """
    Color dodge blend mode.
    Brightens base to reflect over.
    """
    if over >= 1.0:
        result = 1.0
    else:
        result = _clamp(base / (1 - over))
    return _apply_opacity(base, result, opacity)


def blend_color_burn(base: float, over: float, opacity: float = 1.0) -> float:
    """
    Color burn blend mode.
    Darkens base to reflect over.
    """
    if over <= 0.0:
        result = 0.0
    else:
        result = _clamp(1 - (1 - base) / over)
    return _apply_opacity(base, result, opacity)


def blend_linear_dodge(base: float, over: float, opacity: float = 1.0) -> float:
    """
    Linear dodge (same as Add).
    """
    return blend_add(base, over, opacity)


def blend_linear_burn(base: float, over: float, opacity: float = 1.0) -> float:
    """
    Linear burn blend mode.
    Result = Base + Over - 1
    """
    result = _clamp(base + over - 1)
    return _apply_opacity(base, result, opacity)


# ==================== Comparative Blend Modes ====================

def blend_darken(base: float, over: float, opacity: float = 1.0) -> float:
    """
    Darken (Min) blend mode.
    Result = min(Base, Over)
    """
    result = min(base, over)
    return _apply_opacity(base, result, opacity)


def blend_lighten(base: float, over: float, opacity: float = 1.0) -> float:
    """
    Lighten (Max) blend mode.
    Result = max(Base, Over)
    """
    result = max(base, over)
    return _apply_opacity(base, result, opacity)


def blend_exclusion(base: float, over: float, opacity: float = 1.0) -> float:
    """
    Exclusion blend mode.
    Similar to difference but with lower contrast.
    """
    result = base + over - 2 * base * over
    return _apply_opacity(base, result, opacity)


def blend_pin_light(base: float, over: float, opacity: float = 1.0) -> float:
    """
    Pin light blend mode.
    Combines darken and lighten based on over value.
    """
    if over < 0.5:
        result = min(base, 2 * over)
    else:
        result = max(base, 2 * (over - 0.5))
    return _apply_opacity(base, result, opacity)


def blend_hard_mix(base: float, over: float, opacity: float = 1.0) -> float:
    """
    Hard mix blend mode.
    Posterized result based on dodge/burn.
    """
    result = 1.0 if base + over >= 1 else 0.0
    return _apply_opacity(base, result, opacity)


# ==================== Component Blend Modes ====================

def blend_hue(base_rgb: Tuple[float, float, float],
              over_rgb: Tuple[float, float, float],
              opacity: float = 1.0) -> Tuple[float, float, float]:
    """
    Hue blend mode.
    Uses hue from over, saturation and luminosity from base.
    """
    # Convert to HSL
    _, base_s, base_l = rgb_to_hsl(*base_rgb)
    over_h, _, _ = rgb_to_hsl(*over_rgb)

    # Create result with over hue, base sat/lum
    result = hsl_to_rgb(over_h, base_s, base_l)
    return tuple(_apply_opacity(base_rgb[i], result[i], opacity) for i in range(3))


def blend_saturation(base_rgb: Tuple[float, float, float],
                     over_rgb: Tuple[float, float, float],
                     opacity: float = 1.0) -> Tuple[float, float, float]:
    """
    Saturation blend mode.
    Uses saturation from over, hue and luminosity from base.
    """
    base_h, _, base_l = rgb_to_hsl(*base_rgb)
    _, over_s, _ = rgb_to_hsl(*over_rgb)

    result = hsl_to_rgb(base_h, over_s, base_l)
    return tuple(_apply_opacity(base_rgb[i], result[i], opacity) for i in range(3))


def blend_color(base_rgb: Tuple[float, float, float],
                over_rgb: Tuple[float, float, float],
                opacity: float = 1.0) -> Tuple[float, float, float]:
    """
    Color blend mode.
    Uses hue and saturation from over, luminosity from base.
    """
    _, _, base_l = rgb_to_hsl(*base_rgb)
    over_h, over_s, _ = rgb_to_hsl(*over_rgb)

    result = hsl_to_rgb(over_h, over_s, base_l)
    return tuple(_apply_opacity(base_rgb[i], result[i], opacity) for i in range(3))


def blend_luminosity(base_rgb: Tuple[float, float, float],
                     over_rgb: Tuple[float, float, float],
                     opacity: float = 1.0) -> Tuple[float, float, float]:
    """
    Luminosity blend mode.
    Uses luminosity from over, hue and saturation from base.
    """
    base_h, base_s, _ = rgb_to_hsl(*base_rgb)
    _, _, over_l = rgb_to_hsl(*over_rgb)

    result = hsl_to_rgb(base_h, base_s, over_l)
    return tuple(_apply_opacity(base_rgb[i], result[i], opacity) for i in range(3))


# ==================== Color Space Helpers ====================

def rgb_to_hsl(r: float, g: float, b: float) -> Tuple[float, float, float]:
    """Convert RGB (0-1) to HSL (0-1, 0-1, 0-1)."""
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    l = (max_c + min_c) / 2

    if max_c == min_c:
        h = s = 0.0
    else:
        d = max_c - min_c
        s = d / (2 - max_c - min_c) if l > 0.5 else d / (max_c + min_c)

        if max_c == r:
            h = (g - b) / d + (6 if g < b else 0)
        elif max_c == g:
            h = (b - r) / d + 2
        else:
            h = (r - g) / d + 4
        h /= 6

    return h, s, l


def hsl_to_rgb(h: float, s: float, l: float) -> Tuple[float, float, float]:
    """Convert HSL (0-1) to RGB (0-1)."""
    if s == 0:
        return l, l, l

    def hue_to_rgb(p, q, t):
        if t < 0:
            t += 1
        if t > 1:
            t -= 1
        if t < 1/6:
            return p + (q - p) * 6 * t
        if t < 1/2:
            return q
        if t < 2/3:
            return p + (q - p) * (2/3 - t) * 6
        return p

    q = l * (1 + s) if l < 0.5 else l + s - l * s
    p = 2 * l - q

    r = hue_to_rgb(p, q, h + 1/3)
    g = hue_to_rgb(p, q, h)
    b = hue_to_rgb(p, q, h - 1/3)

    return r, g, b


# ==================== Blend Mode Registry ====================

BLEND_MODES: dict[str, Callable] = {
    BlendMode.NORMAL.value: blend_normal,
    BlendMode.MULTIPLY.value: blend_multiply,
    BlendMode.SCREEN.value: blend_screen,
    BlendMode.ADD.value: blend_add,
    BlendMode.DIFFERENCE.value: blend_difference,
    BlendMode.OVERLAY.value: blend_overlay,
    BlendMode.SOFT_LIGHT.value: blend_soft_light,
    BlendMode.HARD_LIGHT.value: blend_hard_light,
    BlendMode.COLOR_DODGE.value: blend_color_dodge,
    BlendMode.COLOR_BURN.value: blend_color_burn,
    BlendMode.LINEAR_DODGE.value: blend_linear_dodge,
    BlendMode.LINEAR_BURN.value: blend_linear_burn,
    BlendMode.DARKEN.value: blend_darken,
    BlendMode.LIGHTEN.value: blend_lighten,
}

# RGB blend modes (require tuple input)
BLEND_MODES_RGB: dict[str, Callable] = {
    BlendMode.HUE.value: blend_hue,
    BlendMode.SATURATION.value: blend_saturation,
    BlendMode.COLOR.value: blend_color,
    BlendMode.LUMINOSITY.value: blend_luminosity,
}


def get_blend_function(mode: BlendMode) -> Callable:
    """Get the blend function for a mode."""
    mode_str = mode.value if isinstance(mode, BlendMode) else mode

    if mode_str in BLEND_MODES:
        return BLEND_MODES[mode_str]
    if mode_str in BLEND_MODES_RGB:
        return BLEND_MODES_RGB[mode_str]

    # Default to normal
    return blend_normal


def apply_blend(mode: BlendMode, base: float, over: float, opacity: float = 1.0) -> float:
    """Apply a blend mode to single values."""
    func = get_blend_function(mode)
    if mode.value in BLEND_MODES_RGB:
        # RGB modes need special handling
        result = func((base, base, base), (over, over, over), opacity)
        return result[0]
    return func(base, over, opacity)

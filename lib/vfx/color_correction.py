"""
Color Correction

Color correction functions for compositing.

Part of Phase 12.1: Compositor (REQ-COMP-03)
"""

from __future__ import annotations
from typing import Tuple, List, Optional, Dict, Any
import math

from .compositor_types import ColorCorrection


def _clamp(value: float, min_val: float = 0.0, max_val: float = 1.0) -> float:
    """Clamp a value to a range."""
    return max(min_val, min(max_val, value))


# ==================== Basic Adjustments ====================

def apply_exposure(value: float, exposure: float) -> float:
    """
    Apply exposure adjustment.
    Exposure is in stops (EV).
    """
    return value * (2 ** exposure)


def apply_gamma(value: float, gamma: float) -> float:
    """
    Apply gamma correction.
    Gamma < 1 brightens, gamma > 1 darkens.
    """
    if gamma <= 0:
        return 0.0
    return value ** (1.0 / gamma)


def apply_contrast(value: float, contrast: float) -> float:
    """
    Apply contrast adjustment.
    Contrast of 1.0 is neutral.
    """
    return _clamp((value - 0.5) * contrast + 0.5)


def apply_saturation(r: float, g: float, b: float, saturation: float) -> Tuple[float, float, float]:
    """
    Apply saturation adjustment.
    Saturation of 1.0 is neutral, 0.0 is grayscale.
    """
    # Convert to grayscale luminance
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b

    # Interpolate between gray and original
    r_out = _clamp(luminance + saturation * (r - luminance))
    g_out = _clamp(luminance + saturation * (g - luminance))
    b_out = _clamp(luminance + saturation * (b - luminance))

    return r_out, g_out, b_out


# ==================== Lift/Gamma/Gain ====================

def apply_lift_gamma_gain(
    value: float,
    lift: float,
    gamma: float,
    gain: float,
) -> float:
    """
    Apply lift/gamma/gain in one operation.

    - Lift: Affects shadows (offset)
    - Gamma: Affects midtones (power)
    - Gain: Affects highlights (multiplier)
    """
    # Apply lift (offset in shadows)
    result = value + lift * (1 - value)

    # Apply gain (multiplier in highlights)
    result = result * gain

    # Apply gamma (power for midtones)
    if gamma > 0 and result > 0:
        result = result ** (1.0 / gamma)

    return _clamp(result)


def apply_lgg_rgb(
    r: float, g: float, b: float,
    lift: Tuple[float, float, float],
    gamma: float,
    gain: Tuple[float, float, float],
) -> Tuple[float, float, float]:
    """Apply per-channel lift/gamma/gain."""
    r_out = apply_lift_gamma_gain(r, lift[0], gamma, gain[0])
    g_out = apply_lift_gamma_gain(g, lift[1], gamma, gain[1])
    b_out = apply_lift_gamma_gain(b, lift[2], gamma, gain[2])
    return r_out, g_out, b_out


# ==================== Offset/Power/Slope (ASC CDL) ====================

def apply_cdl(
    value: float,
    slope: float,
    offset: float,
    power: float,
) -> float:
    """
    Apply ASC CDL (American Society of Cinematographers Color Decision List).

    Formula: (value * slope + offset) ^ power
    """
    result = value * slope + offset
    if result > 0 and power > 0:
        result = result ** power
    return _clamp(result)


def apply_cdl_rgb(
    r: float, g: float, b: float,
    slope: Tuple[float, float, float],
    offset: Tuple[float, float, float],
    power: Tuple[float, float, float],
) -> Tuple[float, float, float]:
    """Apply per-channel ASC CDL."""
    r_out = apply_cdl(r, slope[0], offset[0], power[0])
    g_out = apply_cdl(g, slope[1], offset[1], power[1])
    b_out = apply_cdl(b, slope[2], offset[2], power[2])
    return r_out, g_out, b_out


# ==================== Curves ====================

def apply_curve(value: float, curve_points: List[Tuple[float, float]]) -> float:
    """
    Apply a curve adjustment using linear interpolation.

    Args:
        value: Input value (0-1)
        curve_points: List of (input, output) points defining the curve

    Returns:
        Adjusted value
    """
    if not curve_points:
        return value

    # Sort by input value
    points = sorted(curve_points, key=lambda p: p[0])

    # Find surrounding points
    for i, (x, y) in enumerate(points):
        if value <= x:
            if i == 0:
                return y
            # Linear interpolation
            x0, y0 = points[i - 1]
            x1, y1 = points[i]
            if x1 - x0 == 0:
                return y1
            t = (value - x0) / (x1 - x0)
            return y0 + t * (y1 - y0)

    # Beyond last point
    return points[-1][1]


def apply_rgb_curves(
    r: float, g: float, b: float,
    rgb_curve: List[Tuple[float, float]],
    r_curve: Optional[List[Tuple[float, float]]] = None,
    g_curve: Optional[List[Tuple[float, float]]] = None,
    b_curve: Optional[List[Tuple[float, float]]] = None,
) -> Tuple[float, float, float]:
    """Apply RGB master and individual channel curves."""
    # Apply master curve first
    r = apply_curve(r, rgb_curve)
    g = apply_curve(g, rgb_curve)
    b = apply_curve(b, rgb_curve)

    # Apply individual curves
    if r_curve:
        r = apply_curve(r, r_curve)
    if g_curve:
        g = apply_curve(g, g_curve)
    if b_curve:
        b = apply_curve(b, b_curve)

    return r, g, b


# ==================== Levels ====================

def apply_levels(
    value: float,
    input_black: float = 0.0,
    input_white: float = 1.0,
    gamma: float = 1.0,
    output_black: float = 0.0,
    output_white: float = 1.0,
) -> float:
    """
    Apply levels adjustment.

    1. Expand input range (black/white point)
    2. Apply gamma
    3. Compress to output range
    """
    # Input range expansion
    if input_white != input_black:
        result = (value - input_black) / (input_white - input_black)
    else:
        result = 0.5

    result = _clamp(result)

    # Gamma
    if gamma > 0 and result > 0:
        result = result ** (1.0 / gamma)

    # Output range compression
    result = result * (output_white - output_black) + output_black

    return _clamp(result)


# ==================== HSV Adjustments ====================

def rgb_to_hsv(r: float, g: float, b: float) -> Tuple[float, float, float]:
    """Convert RGB to HSV."""
    max_c = max(r, g, b)
    min_c = min(r, g, b)
    diff = max_c - min_c

    v = max_c

    if max_c == min_c:
        h = 0.0
    elif max_c == r:
        h = (60 * ((g - b) / diff) + 360) % 360
    elif max_c == g:
        h = (60 * ((b - r) / diff) + 120) % 360
    else:
        h = (60 * ((r - g) / diff) + 240) % 360

    s = 0.0 if max_c == 0 else diff / max_c

    return h / 360.0, s, v  # Normalize H to 0-1


def hsv_to_rgb(h: float, s: float, v: float) -> Tuple[float, float, float]:
    """Convert HSV to RGB."""
    h = h * 360  # Convert to degrees

    if s == 0:
        return v, v, v

    i = int(h // 60) % 6
    f = (h / 60) - int(h // 60)
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)

    if i == 0:
        return v, t, p
    elif i == 1:
        return q, v, p
    elif i == 2:
        return p, v, t
    elif i == 3:
        return p, q, v
    elif i == 4:
        return t, p, v
    else:
        return v, p, q


def apply_hsv_adjustment(
    r: float, g: float, b: float,
    hue_shift: float = 0.0,
    saturation_mult: float = 1.0,
    value_mult: float = 1.0,
) -> Tuple[float, float, float]:
    """
    Apply HSV adjustments.

    Args:
        r, g, b: Input RGB values (0-1)
        hue_shift: Hue rotation (-0.5 to 0.5)
        saturation_mult: Saturation multiplier
        value_mult: Value/brightness multiplier
    """
    h, s, v = rgb_to_hsv(r, g, b)

    # Apply adjustments
    h = (h + hue_shift + 1.0) % 1.0
    s = _clamp(s * saturation_mult)
    v = _clamp(v * value_mult)

    return hsv_to_rgb(h, s, v)


# ==================== Temperature/Tint ====================

def apply_white_balance(
    r: float, g: float, b: float,
    temperature: float = 0.0,
    tint: float = 0.0,
) -> Tuple[float, float, float]:
    """
    Apply white balance adjustment.

    Args:
        temperature: -100 (cool/blue) to +100 (warm/yellow)
        tint: -100 (green) to +100 (magenta)
    """
    # Temperature affects blue-yellow axis
    temp_factor = temperature / 100.0
    r_out = r * (1 + temp_factor * 0.1)
    b_out = b * (1 - temp_factor * 0.1)

    # Tint affects green-magenta axis
    tint_factor = tint / 100.0
    g_out = g * (1 - abs(tint_factor) * 0.05)
    if tint_factor > 0:
        # Magenta - add to R and B
        r_out = r_out * (1 + tint_factor * 0.03)
        b_out = b_out * (1 + tint_factor * 0.03)
    else:
        # Green - already handled above
        pass

    return _clamp(r_out), _clamp(g_out), _clamp(b_out)


# ==================== Highlights/Shadows ====================

def apply_highlights_shadows(
    value: float,
    highlights: float = 0.0,
    shadows: float = 0.0,
) -> float:
    """
    Apply highlights and shadows adjustment.

    Args:
        value: Input value (0-1)
        highlights: -100 to +100 (affects bright areas)
        shadows: -100 to +100 (affects dark areas)
    """
    # Create luminance-based masks
    shadow_mask = 1 - value  # Higher for dark areas
    highlight_mask = value  # Higher for bright areas

    # Apply adjustments
    shadow_adj = shadows / 100.0 * 0.3
    highlight_adj = highlights / 100.0 * 0.3

    result = value
    result += shadow_adj * shadow_mask
    result += highlight_adj * highlight_mask

    return _clamp(result)


# ==================== Combined Color Correction ====================

def apply_color_correction(
    r: float, g: float, b: float,
    cc: ColorCorrection,
) -> Tuple[float, float, float]:
    """
    Apply all color correction settings.

    Applies in order:
    1. Temperature/tint (white balance)
    2. Exposure
    3. Highlights/shadows
    4. Lift/gamma/gain
    5. Contrast
    6. Saturation
    7. HSV adjustments
    """
    # 1. White balance
    r, g, b = apply_white_balance(r, g, b, cc.temperature, cc.tint)

    # 2. Exposure
    r = apply_exposure(r, cc.exposure)
    g = apply_exposure(g, cc.exposure)
    b = apply_exposure(b, cc.exposure)

    # 3. Highlights/shadows (per channel)
    r = apply_highlights_shadows(r, cc.highlights, cc.shadows)
    g = apply_highlights_shadows(g, cc.highlights, cc.shadows)
    b = apply_highlights_shadows(b, cc.highlights, cc.shadows)

    # 4. Lift/gamma/gain
    r, g, b = apply_lgg_rgb(r, g, b, cc.lift, cc.gamma, cc.gain)

    # 5. Contrast
    r = apply_contrast(r, cc.contrast)
    g = apply_contrast(g, cc.contrast)
    b = apply_contrast(b, cc.contrast)

    # 6. Saturation
    r, g, b = apply_saturation(r, g, b, cc.saturation)

    # 7. HSV adjustments (if non-default)
    if cc.hue_shift != 0:
        r, g, b = apply_hsv_adjustment(r, g, b, cc.hue_shift)

    return _clamp(r), _clamp(g), _clamp(b)


# ==================== Presets ====================

COLOR_PRESETS: Dict[str, Dict[str, Any]] = {
    "neutral": {
        "exposure": 0.0,
        "contrast": 1.0,
        "saturation": 1.0,
        "gamma": 1.0,
    },
    "cinematic_warm": {
        "temperature": 25,
        "tint": 5,
        "contrast": 1.1,
        "saturation": 0.9,
        "shadows": -10,
    },
    "cinematic_cool": {
        "temperature": -20,
        "tint": -5,
        "contrast": 1.15,
        "saturation": 0.85,
        "highlights": -15,
    },
    "high_contrast": {
        "contrast": 1.4,
        "saturation": 1.1,
        "blacks": -20,
        "whites": 15,
    },
    "low_contrast": {
        "contrast": 0.8,
        "saturation": 0.9,
        "blacks": 15,
        "highlights": -10,
    },
    "vintage": {
        "temperature": 15,
        "saturation": 0.8,
        "contrast": 0.95,
        "blacks": 10,
    },
    "bleach_bypass": {
        "contrast": 1.2,
        "saturation": 0.5,
        "gamma": 0.9,
    },
}


def get_color_preset(name: str) -> Dict[str, Any]:
    """Get a color correction preset by name."""
    return COLOR_PRESETS.get(name, COLOR_PRESETS["neutral"]).copy()


def apply_preset(cc: ColorCorrection, preset_name: str) -> ColorCorrection:
    """Apply a preset to a ColorCorrection object."""
    preset = get_color_preset(preset_name)

    for key, value in preset.items():
        if hasattr(cc, key):
            setattr(cc, key, value)

    return cc

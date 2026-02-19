"""
Type-Safe Enumerations for Cinematic System

Defines enums for lens types, light types, quality tiers,
color spaces, and animation easing functions.
"""

from __future__ import annotations
from enum import Enum


class LensType(Enum):
    """
    Lens focal length presets.

    Common focal lengths for product and portrait photography.
    """
    WIDE_14MM = "14mm_ultra_wide"
    WIDE_24MM = "24mm_wide"
    NORMAL_35MM = "35mm_documentary"
    NORMAL_50MM = "50mm_normal"
    PORTRAIT_85MM = "85mm_portrait"
    TELEPHOTO_135MM = "135mm_telephoto"
    MACRO_90MM = "90mm_macro"


class LightType(Enum):
    """
    Light types for cinematic lighting.

    Maps to Blender light types.
    """
    AREA = "area"
    SPOT = "spot"
    POINT = "point"
    SUN = "sun"


class AreaLightShape(Enum):
    """
    Shape options for area lights.

    Maps to Blender area light shapes (must be uppercase).
    """
    SQUARE = "SQUARE"
    RECTANGLE = "RECTANGLE"
    DISK = "DISK"
    ELLIPSE = "ELLIPSE"


class QualityTier(Enum):
    """
    Render quality tiers.

    Ordered from fastest to highest quality.
    """
    VIEWPORT_CAPTURE = "viewport_capture"
    EEVEE_DRAFT = "eevee_draft"
    CYCLES_PREVIEW = "cycles_preview"
    CYCLES_PRODUCTION = "cycles_production"
    CYCLES_ARCHIVE = "cycles_archive"


class ColorSpace(Enum):
    """
    Color space options for rendering.

    AgX is the modern Blender default (4.0+).
    """
    SRGB = "srgb"
    AGX = "AgX"
    ACESCG = "ACEScg"
    FILMIC = "Filmic"


class EasingType(Enum):
    """
    Animation easing functions.

    For camera movements and transitions.
    """
    LINEAR = "linear"
    EASE_IN = "ease_in"
    EASE_OUT = "ease_out"
    EASE_IN_OUT = "ease_in_out"


class ViewTransform(str, Enum):
    """
    Blender view transform options.

    Controls how scene-linear color is transformed for display.
    AgX is the modern default (Blender 4.0+).
    """
    STANDARD = "Standard"
    AGX = "AgX"
    FILMIC = "Filmic"
    FILMIC_LOG = "Filmic Log"
    RAW = "Raw"
    LOG = "Log"
    ACESCG = "ACEScg"


class WorkingColorSpace(str, Enum):
    """
    Scene linear working color space options.

    Determines the internal color space used for rendering calculations.
    Configured via Blender's Scene > Color Management > Render Space.
    """
    AGX = "AgX"
    ACESCG = "ACEScg"
    FILMIC = "Filmic"
    STANDARD = "Standard"

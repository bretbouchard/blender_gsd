"""
Animation Module for Blender 5.0+.

Provides utilities for shape keys, dope sheet operations,
and animation workflow enhancements.

Example:
    >>> from lib.blender5x.animation import ShapeKeyTools, DopeSheetTools
    >>> ShapeKeyTools.create_morph_target(mesh, "Smile")
    >>> DopeSheetTools.select_keyframes(obj, frame_range=(1, 100))
"""

from .shape_keys import (
    ShapeKeyTools,
    ShapeKeyInfo,
    ShapeKeyInterpolation,
)

from .dope_sheet import (
    DopeSheetTools,
    ChannelGroup,
    DopeSheetMode,
    KeyframeHandleType,
    KeyframeInfo,
)

__all__ = [
    # Shape Keys
    "ShapeKeyTools",
    "ShapeKeyInfo",
    "ShapeKeyInterpolation",
    # Dope Sheet
    "DopeSheetTools",
    "ChannelGroup",
    "DopeSheetMode",
    "KeyframeHandleType",
    "KeyframeInfo",
]

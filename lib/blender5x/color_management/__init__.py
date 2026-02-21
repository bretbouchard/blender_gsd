"""
Color Management Module for Blender 5.0+.

Provides ACES 1.3/2.0 color management, HDR video export,
and view transform utilities for professional color workflows.

Example:
    >>> from lib.blender5x.color_management import ACESWorkflow, HDRVideoExport
    >>> ACESWorkflow.setup_acescg()
    >>> HDRVideoExport.configure_h264_hdr(transfer="PQ")
"""

from .aces import (
    ACESWorkflow,
    HDRVideoExport,
    HDRMetadata,
    ACES_VIEWS_13,
    ACES_VIEWS_20,
    DISPLAY_DEVICES,
)

from .hdr_export import (
    HDRExport,
    HDRFormat,
    TransferFunction,
    DynamicRangeInfo,
    HDRMonitorSettings,
    HDR_MONITOR_PRESETS,
)

from .view_transforms import (
    ViewTransforms,
    ViewTransformInfo,
    ViewTransformCategory,
    FilmicControls,
    BUILTIN_TRANSFORMS,
)

__all__ = [
    # ACES
    "ACESWorkflow",
    "HDRVideoExport",
    "HDRMetadata",
    "ACES_VIEWS_13",
    "ACES_VIEWS_20",
    "DISPLAY_DEVICES",
    # HDR Export
    "HDRExport",
    "HDRFormat",
    "TransferFunction",
    "DynamicRangeInfo",
    "HDRMonitorSettings",
    "HDR_MONITOR_PRESETS",
    # View Transforms
    "ViewTransforms",
    "ViewTransformInfo",
    "ViewTransformCategory",
    "FilmicControls",
    "BUILTIN_TRANSFORMS",
]

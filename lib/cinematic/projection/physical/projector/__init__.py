"""
Projector Profile and Calibration Module

This module provides projector hardware profiles and calibration
utilities for physical projection mapping.
"""

from .profiles import (
    ProjectorType,
    AspectRatio,
    LensShift,
    KeystoneCorrection,
    ProjectorProfile,
)

from .calibration import (
    throw_ratio_to_focal_length,
    focal_length_to_throw_ratio,
    calculate_throw_distance,
    calculate_image_width,
    create_projector_camera,
    configure_render_for_projector,
    restore_render_settings,
)

__all__ = [
    # Enums
    "ProjectorType",
    "AspectRatio",

    # Data classes
    "LensShift",
    "KeystoneCorrection",
    "ProjectorProfile",

    # Calibration functions
    "throw_ratio_to_focal_length",
    "focal_length_to_throw_ratio",
    "calculate_throw_distance",
    "calculate_image_width",
    "create_projector_camera",
    "configure_render_for_projector",
    "restore_render_settings",
]

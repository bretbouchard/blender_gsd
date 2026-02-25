"""
Physical Projector Mapping Module

This module provides tools for mapping physical projector hardware
to real-world projection surfaces.

Key Components:
- ProjectorProfile: Hardware specifications for real projectors
- Calibration: Throw ratio to focal length conversion
- Stage Functions: Pipeline stages for projection mapping workflow

Part of Milestone v0.15 - Physical Projector Mapping System

Usage:
    from lib.cinematic.projection.physical import (
        # Types
        ProjectorProfile,
        ProjectorType,
        AspectRatio,
        LensShift,
        KeystoneCorrection,

        # Calibration functions
        throw_ratio_to_focal_length,
        focal_length_to_throw_ratio,
        calculate_throw_distance,
        calculate_image_width,
        create_projector_camera,
        configure_render_for_projector,
        restore_render_settings,
    )

    # Create a projector profile
    profile = ProjectorProfile(
        name="Epson_Home_Cinema_2150",
        manufacturer="Epson",
        throw_ratio=1.32,
        native_resolution=(1920, 1080),
        sensor_width=36.0,
        sensor_height=20.25,
    )

    # Get Blender focal length from throw ratio
    focal_length = profile.get_blender_focal_length()

    # Create a Blender camera matching the projector
    camera = create_projector_camera(profile)
"""

from .projector.profiles import (
    # Enums
    ProjectorType,
    AspectRatio,

    # Data classes
    LensShift,
    KeystoneCorrection,
    ProjectorProfile,
)

from .projector.calibration import (
    # Calibration functions
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

__version__ = "0.1.0"

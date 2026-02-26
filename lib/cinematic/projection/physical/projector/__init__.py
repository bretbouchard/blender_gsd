"""Physical projector mapping module.

This module provides projector hardware profiles, calibration utilities,
and camera factory functions for physical projection mapping.

Key Formula (Geometry Rick verified):
    focal_length = sensor_width * throw_ratio

NOT: focal_length = (throw_ratio * sensor_width) / 2

Usage:
    from lib.cinematic.projection.physical.projector import (
        ProjectorProfile,
        get_profile,
        create_projector_camera,
    )

    # Get a projector profile
    profile = get_profile("Epson_Home_Cinema_2150")

    # Create Blender camera from profile
    camera = create_projector_camera(profile)
"""

# Profile types
from .profiles import (
    ProjectorProfile,
    ProjectorType,
    AspectRatio,
    LensShift,
    KeystoneCorrection,
)

# Profile database
from .profile_database import (
    PROJECTOR_PROFILES,
    get_profile,
    list_profiles,
    get_profiles_by_throw_ratio,
    get_profiles_by_resolution,
    get_short_throw_profiles,
    get_4k_profiles,
    load_profile,
    load_profile_from_yaml,
)

# Calibration utilities
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
    # Types
    'ProjectorProfile',
    'ProjectorType',
    'AspectRatio',
    'LensShift',
    'KeystoneCorrection',

    # Database
    'PROJECTOR_PROFILES',
    'get_profile',
    'list_profiles',
    'get_profiles_by_throw_ratio',
    'get_profiles_by_resolution',
    'get_short_throw_profiles',
    'get_4k_profiles',
    'load_profile',
    'load_profile_from_yaml',

    # Calibration
    'throw_ratio_to_focal_length',
    'focal_length_to_throw_ratio',
    'calculate_throw_distance',
    'calculate_image_width',
    'create_projector_camera',
    'configure_render_for_projector',
    'restore_render_settings',
]

__version__ = '0.1.0'

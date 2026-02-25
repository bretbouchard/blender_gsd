"""Physical projector mapping system.

This package provides tools for mapping content to physical projectors
in real-world environments.

Components:
- projector: Hardware profiles and calibration utilities
- stages: Pipeline stage functions (Phase 18.1+)
- targets: Projection surface configurations (Phase 18.3+)
- shaders: Camera projection shader nodes (Phase 18.2+)

Workflow:
1. Select projector profile from database
2. Create Blender camera from profile
3. Calibrate to real-world surface (Phase 18.1)
4. Map content to surface (Phase 18.2)
5. Render at projector native resolution

Example:
    from lib.cinematic.projection.physical import (
        get_profile,
        create_projector_camera,
    )

    # Setup projector
    profile = get_profile("Epson_Home_Cinema_2150")
    camera = create_projector_camera(profile)

    # Position camera to match real-world projector location
    camera.location = (2.5, 0, 1.8)
    camera.rotation_euler = (math.radians(-15), 0, 0)
"""

from .projector import (
    # Re-export all projector module items
    ProjectorProfile,
    ProjectorType,
    AspectRatio,
    LensShift,
    KeystoneCorrection,
    PROJECTOR_PROFILES,
    get_profile,
    list_profiles,
    get_profiles_by_throw_ratio,
    get_profiles_by_resolution,
    get_short_throw_profiles,
    get_4k_profiles,
    load_profile_from_yaml,
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

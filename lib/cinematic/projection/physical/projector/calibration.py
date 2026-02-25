"""Calibration utilities for physical projector mapping.

This module provides the throw ratio to focal length conversion
and camera factory functions for creating Blender cameras that
match physical projector optical characteristics.

Key Formula (Geometry Rick verified):
    focal_length = sensor_width * throw_ratio

The original formula had an incorrect division by 2, which was
identified and corrected by Geometry Rick during the design review.

Part of Milestone v0.15 - Physical Projector Mapping System
"""

import math
from typing import Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    import bpy
    from mathutils import Vector

from .profiles import ProjectorProfile, ProjectorType


def throw_ratio_to_focal_length(
    throw_ratio: float,
    sensor_width: float,
    sensor_height: float,
    aspect: str = 'horizontal'
) -> float:
    """Convert throw ratio to Blender focal length.

    CORRECTED FORMULA (Geometry Rick identified original was wrong):
        focal_length = sensor_width * throw_ratio

    The original formula had an incorrect division by 2.

    Throw ratio is defined as:
        throw_ratio = throw_distance / image_width

    For a camera with sensor_width at focal_length projecting an image
    at throw_distance, the image width is:
        image_width = throw_distance * sensor_width / focal_length

    Therefore:
        throw_ratio = throw_distance / (throw_distance * sensor_width / focal_length)
        throw_ratio = focal_length / sensor_width
        focal_length = sensor_width * throw_ratio

    Args:
        throw_ratio: Projector throw ratio (distance / image_width)
        sensor_width: Sensor width in mm
        sensor_height: Sensor height in mm
        aspect: 'horizontal', 'vertical', or 'diagonal'

    Returns:
        Focal length in mm for Blender camera

    Raises:
        ValueError: If throw_ratio <= 0 or aspect invalid
    """
    if throw_ratio <= 0:
        raise ValueError(f"Throw ratio must be positive, got {throw_ratio}")

    if aspect == 'horizontal':
        return sensor_width * throw_ratio
    elif aspect == 'vertical':
        # Vertical throw ratio relates to sensor height
        # Convert to horizontal-equivalent focal length
        return sensor_height * throw_ratio * (sensor_width / sensor_height)
    elif aspect == 'diagonal':
        diagonal = math.sqrt(sensor_width**2 + sensor_height**2)
        return diagonal * throw_ratio
    else:
        raise ValueError(
            f"Invalid aspect: {aspect}. Use 'horizontal', 'vertical', or 'diagonal'"
        )


def focal_length_to_throw_ratio(
    focal_length: float,
    sensor_width: float
) -> float:
    """Convert Blender focal length back to throw ratio.

    Inverse of throw_ratio_to_focal_length.

    Args:
        focal_length: Focal length in mm
        sensor_width: Sensor width in mm

    Returns:
        Throw ratio (distance / width)

    Raises:
        ValueError: If focal_length <= 0
    """
    if focal_length <= 0:
        raise ValueError(f"Focal length must be positive, got {focal_length}")

    return focal_length / sensor_width


def calculate_throw_distance(
    throw_ratio: float,
    image_width: float
) -> float:
    """Calculate throw distance for desired image width.

    Args:
        throw_ratio: Projector throw ratio
        image_width: Desired image width in meters

    Returns:
        Required throw distance in meters

    Raises:
        ValueError: If throw_ratio <= 0 or image_width <= 0
    """
    if throw_ratio <= 0:
        raise ValueError(f"Throw ratio must be positive, got {throw_ratio}")
    if image_width <= 0:
        raise ValueError(f"Image width must be positive, got {image_width}")

    return throw_ratio * image_width


def calculate_image_width(
    throw_ratio: float,
    throw_distance: float
) -> float:
    """Calculate image width at given throw distance.

    Args:
        throw_ratio: Projector throw ratio
        throw_distance: Distance from projector to surface in meters

    Returns:
        Image width in meters

    Raises:
        ValueError: If throw_ratio <= 0 or throw_distance <= 0
    """
    if throw_ratio <= 0:
        raise ValueError(f"Throw ratio must be positive, got {throw_ratio}")
    if throw_distance <= 0:
        raise ValueError(f"Throw distance must be positive, got {throw_distance}")

    return throw_distance / throw_ratio


def create_projector_camera(
    profile: ProjectorProfile,
    name: Optional[str] = None,
    collection: Optional['bpy.types.Collection'] = None
) -> 'bpy.types.Object':
    """Create a Blender camera from a projector profile.

    This creates a camera that matches the optical characteristics
    of the physical projector for accurate preview and rendering.

    Note: This function requires Blender's bpy module and will
    raise ImportError if run outside of Blender.

    Args:
        profile: ProjectorProfile with optical characteristics
        name: Camera name (defaults to profile.name + "_camera")
        collection: Collection to link camera to (defaults to scene collection)

    Returns:
        Blender camera object

    Raises:
        ImportError: If bpy is not available (not running in Blender)
    """
    try:
        import bpy
    except ImportError as e:
        raise ImportError(
            "create_projector_camera requires Blender's bpy module. "
            "This function can only be used within Blender."
        ) from e

    camera_name = name or f"{profile.name}_camera"

    # Create camera data
    cam_data = bpy.data.cameras.new(camera_name)
    cam_data.type = 'PERSP'

    # Set focal length from throw ratio
    cam_data.lens = profile.get_blender_focal_length()

    # Set sensor size
    cam_data.sensor_width = profile.sensor_width
    cam_data.sensor_height = profile.sensor_height
    cam_data.sensor_fit = 'HORIZONTAL'

    # Set lens shift
    cam_data.shift_x = profile.get_blender_shift_x()
    cam_data.shift_y = profile.get_blender_shift_y()

    # Create camera object
    cam_obj = bpy.data.objects.new(camera_name, cam_data)

    # Link to collection
    if collection is None:
        collection = bpy.context.scene.collection
    collection.objects.link(cam_obj)

    # Store profile reference as custom property
    cam_obj['projector_profile'] = profile.name
    cam_obj['throw_ratio'] = profile.throw_ratio

    return cam_obj


def configure_render_for_projector(
    profile: ProjectorProfile,
    scene: Optional['bpy.types.Scene'] = None
) -> dict:
    """Configure render settings for projector output.

    Note: This function requires Blender's bpy module and will
    raise ImportError if run outside of Blender.

    Args:
        profile: ProjectorProfile with resolution
        scene: Scene to configure (defaults to active scene)

    Returns:
        Dict with original settings for restoration

    Raises:
        ImportError: If bpy is not available (not running in Blender)
    """
    try:
        import bpy
    except ImportError as e:
        raise ImportError(
            "configure_render_for_projector requires Blender's bpy module. "
            "This function can only be used within Blender."
        ) from e

    if scene is None:
        scene = bpy.context.scene

    # Store original settings
    original = {
        'resolution_x': scene.render.resolution_x,
        'resolution_y': scene.render.resolution_y,
        'resolution_percentage': scene.render.resolution_percentage,
        'pixel_aspect_x': scene.render.pixel_aspect_x,
        'pixel_aspect_y': scene.render.pixel_aspect_y,
    }

    # Set to projector native resolution
    scene.render.resolution_x = profile.native_resolution[0]
    scene.render.resolution_y = profile.native_resolution[1]
    scene.render.resolution_percentage = 100
    scene.render.pixel_aspect_x = 1.0
    scene.render.pixel_aspect_y = 1.0

    return original


def restore_render_settings(
    original: dict,
    scene: Optional['bpy.types.Scene'] = None
) -> None:
    """Restore render settings from saved state.

    Args:
        original: Dict from configure_render_for_projector
        scene: Scene to restore (defaults to active scene)

    Raises:
        ImportError: If bpy is not available (not running in Blender)
    """
    try:
        import bpy
    except ImportError as e:
        raise ImportError(
            "restore_render_settings requires Blender's bpy module. "
            "This function can only be used within Blender."
        ) from e

    if scene is None:
        scene = bpy.context.scene

    scene.render.resolution_x = original['resolution_x']
    scene.render.resolution_y = original['resolution_y']
    scene.render.resolution_percentage = original['resolution_percentage']
    scene.render.pixel_aspect_x = original['pixel_aspect_x']
    scene.render.pixel_aspect_y = original['pixel_aspect_y']

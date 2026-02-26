"""
Keystone correction utilities for physical projector mapping.

Computes and applies keystone correction via lens shift.
"""

import math
from typing import Tuple

from .alignment import Vector3


def compute_keystone_correction(
    surface_normal: Tuple[float, float, float],
    projector_direction: Tuple[float, float, float],
    distance_to_surface: float
) -> Tuple[float, float]:
    """
    Compute keystone correction values from surface/projector alignment.

    Keystone correction is needed when the projector is not perpendicular
    to the projection surface. The amount of keystone depends on:
    1. Angle between projector direction and surface normal
    2. Distance to the surface

    Args:
        surface_normal: Normal vector of the projection surface
        projector_direction: Direction the projector is pointing
        distance_to_surface: Distance from projector to surface (meters)

    Returns:
        (horizontal_keystone, vertical_keystone) in degrees
    """
    # Convert to Vector3
    normal = Vector3.from_tuple(surface_normal).normalized()
    direction = Vector3.from_tuple(projector_direction).normalized()

    # Angle between projector and surface normal
    dot = direction.dot(normal)
    angle = math.acos(max(-1.0, min(1.0, dot)))  # Clamp for numerical stability

    # Decompose angle into approximate H/V components
    # This is simplified - real keystone depends on projector orientation
    # For a projector pointed at a surface at an angle:
    # - Horizontal keystone: rotation around vertical axis
    # - Vertical keystone: rotation around horizontal axis

    # Simplified model: keystone ~ angle * 0.5 (rough approximation)
    keystone_factor = angle * 0.5

    # Compute components based on projector orientation
    # Project the normal onto the projector's local axes
    # Horizontal component (left/right tilt)
    h_component = abs(normal.x) * keystone_factor
    # Vertical component (up/down tilt)
    v_component = abs(normal.y) * keystone_factor

    # Convert to degrees
    h_keystone = math.degrees(h_component)
    v_keystone = math.degrees(v_component)

    return (h_keystone, v_keystone)


def keystone_angle_to_shift(keystone_degrees: float, throw_ratio: float) -> float:
    """
    Convert keystone angle to lens shift percentage.

    Lens shift is expressed as a fraction of the image dimension.
    For example, a shift of 0.15 means the15% shift.

    Args:
        keystone_degrees: Keystone angle in degrees
        throw_ratio: Projector throw ratio

    Returns:
        Lens shift as a fraction (e.g., 0.15 for 15%)
    """
    # Simplified conversion: tan(angle) * factor
    # The factor depends on throw ratio - longer throw = less shift needed
    factor = 1.0 / max(0.5, throw_ratio)

    angle_rad = math.radians(keystone_degrees)
    shift = math.tan(angle_rad) * factor

    # Limit to reasonable range (typically +/- 20%)
    return max(-0.2, min(0.2, shift))


def apply_keystone_to_camera(
    camera,
    h_keystone: float,
    v_keystone: float,
    throw_ratio: float = 1.0
) -> None:
    """
    Apply keystone correction to a Blender camera via lens shift.

    Note: This function requires bpy (Blender Python API).
    For testing without Blender, use the pure Python version.

    Args:
        camera: Blender camera object
        h_keystone: Horizontal keystone angle in degrees
        v_keystone: Vertical keystone angle in degrees
        throw_ratio: Projector throw ratio (for shift calculation)
    """
    try:
        import bpy
    except ImportError:
        raise ImportError(
            "apply_keystone_to_camera requires Blender (bpy). "
            "Use keystone_angle_to_shift() for pure Python calculation."
        )

    # Compute shift values
    shift_x = keystone_angle_to_shift(h_keystone, throw_ratio)
    shift_y = keystone_angle_to_shift(v_keystone, throw_ratio)

    # Apply to camera
    camera.data.shift_x = shift_x
    camera.data.shift_y = shift_y

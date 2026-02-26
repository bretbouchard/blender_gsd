"""
Surface transform calculator for projector-to-surface mapping.

Computes complete transform from alignment data for use in the calibration workflow.
"""

from dataclasses import dataclass
from typing import Tuple, Optional, List

from .alignment import AlignmentResult, Vector3


@dataclass
class SurfaceTransform:
    """Complete transform from projector to surface."""
    projector_to_world: Optional[List[List[float]]]  # 4x4 matrix as list of lists
    surface_normal: Tuple[float, float, float]
    surface_bounds: Tuple[Tuple[float, float, float], Tuple[float, float, float]]  # (min, max)
    projection_center: Tuple[float, float, float]
    calibration_error: float = 0.0
    is_valid: bool = False


def calculate_surface_transform(
    alignment_result: AlignmentResult,
    surface_width: float = 1.0,
    surface_height: float = 1.0
) -> SurfaceTransform:
    """
    Calculate complete surface transform from calibration data.

    This is the main entry point for projector-to-surface mapping.

    Args:
        alignment_result: Result from 3-point or 4-point alignment
        surface_width: Width of the projection surface (meters)
        surface_height: Height of the projection surface (meters)

    Returns:
        SurfaceTransform ready for use in calibration workflow
    """
    # Extract transform from alignment result
    transform = alignment_result.transform

    # Compute surface normal from rotation matrix diagonal
    rot_x = transform.data[0][0]
    rot_y = transform.data[1][1]
    rot_z = transform.data[2][2]

    surface_normal = (rot_x, rot_y, rot_z)

    # Compute surface bounds in world space
    # Transform the four corners of the projection surface
    corners_projector = [
        Vector3(0, 0, 0),           # Bottom-left
        Vector3(1, 0, 0),           # Bottom-right
        Vector3(0, 1, 0),           # Top-left
        Vector3(1, 1, 0),           # Top-right
    ]

    corners_world = [transform.transform_point(c) for c in corners_projector]

    # Compute bounding box
    min_corner = Vector3(
        min(c.x for c in corners_world),
        min(c.y for c in corners_world),
        min(c.z for c in corners_world),
    )
    max_corner = Vector3(
        max(c.x for c in corners_world),
        max(c.y for c in corners_world),
        max(c.z for c in corners_world),
    )

    surface_bounds = (min_corner.to_tuple(), max_corner.to_tuple())

    # Projection center is at center of surface (in world space)
    center_world = transform.transform_point(Vector3(0.5, 0.5, 0))
    projection_center = center_world.to_tuple()

    return SurfaceTransform(
        projector_to_world=transform.to_list(),
        surface_normal=surface_normal,
        surface_bounds=surface_bounds,
        projection_center=projection_center,
        calibration_error=alignment_result.error,
        is_valid=True
    )

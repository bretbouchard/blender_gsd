"""
Projection Utilities

Helper functions for anamorphic projection system.

Part of Phase 9.0 - Projection Foundation (REQ-ANAM-01)
"""

from __future__ import annotations
import math
from typing import Tuple, List, Optional

from .types import SurfaceType, SurfaceInfo

# Blender API guard
try:
    import bpy
    import mathutils
    from mathutils import Vector
    HAS_BLENDER = True
except ImportError:
    HAS_BLENDER = False
    Vector = None


def classify_surface_type(normal: Tuple[float, float, float]) -> SurfaceType:
    """
    Classify a surface type based on its normal vector.

    Args:
        normal: Surface normal (normalized)

    Returns:
        SurfaceType enum value
    """
    nx, ny, nz = normal

    # Z-component determines floor/ceiling vs wall
    if nz > 0.7:
        return SurfaceType.FLOOR
    elif nz < -0.7:
        return SurfaceType.CEILING
    elif abs(nz) < 0.3:
        return SurfaceType.WALL
    else:
        return SurfaceType.CUSTOM


def is_surface_in_frustum(
    surface_center: Tuple[float, float, float],
    camera_position: Tuple[float, float, float],
    camera_forward: Tuple[float, float, float],
    fov_degrees: float,
) -> bool:
    """
    Check if a surface center is within camera frustum.

    Simplified check - only considers forward direction and FOV.

    Args:
        surface_center: World position of surface center
        camera_position: Camera world position
        camera_forward: Camera forward direction (normalized)
        fov_degrees: Camera field of view in degrees

    Returns:
        True if surface is roughly in frustum
    """
    # Vector from camera to surface
    to_surface = (
        surface_center[0] - camera_position[0],
        surface_center[1] - camera_position[1],
        surface_center[2] - camera_position[2],
    )

    # Normalize
    length = math.sqrt(sum(v * v for v in to_surface))
    if length < 0.001:
        return False

    to_surface_norm = tuple(v / length for v in to_surface)

    # Dot product with camera forward
    dot = sum(a * b for a, b in zip(camera_forward, to_surface_norm))

    # Must be in front of camera (positive dot)
    if dot < 0:
        return False

    # Check angle against FOV
    half_fov_rad = math.radians(fov_degrees / 2)
    cos_half_fov = math.cos(half_fov_rad)

    return dot > cos_half_fov


def calculate_projection_scale(
    camera_distance: float,
    fov_degrees: float,
    image_width: int,
) -> float:
    """
    Calculate the scale of projection at a given distance.

    Args:
        camera_distance: Distance from camera to surface
        fov_degrees: Camera field of view
        image_width: Source image width in pixels

    Returns:
        Width of projected image at that distance (in meters)
    """
    half_fov_rad = math.radians(fov_degrees / 2)
    half_width = camera_distance * math.tan(half_fov_rad)
    return half_width * 2


def get_projection_bounds(
    camera_position: Tuple[float, float, float],
    camera_rotation: Tuple[float, float, float],
    fov_degrees: float,
    near_distance: float,
    far_distance: float,
    aspect_ratio: float = 16 / 9,
) -> List[Tuple[float, float, float]]:
    """
    Calculate the 8 corners of the camera frustum.

    Useful for visualization and debugging.

    Args:
        camera_position: Camera world position
        camera_rotation: Euler rotation in degrees (XYZ)
        fov_degrees: Vertical field of view
        near_distance: Near clip distance
        far_distance: Far clip distance
        aspect_ratio: Width / height

    Returns:
        List of 8 corner positions in world space
    """
    if not HAS_BLENDER:
        return []

    # Create rotation
    rot_rad = [math.radians(r) for r in camera_rotation]
    euler = mathutils.Euler(rot_rad, 'XYZ')

    # Half FOV
    half_fov = math.radians(fov_degrees / 2)

    # Calculate half-sizes at near and far
    near_half_height = near_distance * math.tan(half_fov)
    near_half_width = near_half_height * aspect_ratio
    far_half_height = far_distance * math.tan(half_fov)
    far_half_width = far_half_height * aspect_ratio

    # Local corners
    local_corners = [
        (-near_half_width, -near_half_height, -near_distance),
        (near_half_width, -near_half_height, -near_distance),
        (near_half_width, near_half_height, -near_distance),
        (-near_half_width, near_half_height, -near_distance),
        (-far_half_width, -far_half_height, -far_distance),
        (far_half_width, -far_half_height, -far_distance),
        (far_half_width, far_half_height, -far_distance),
        (-far_half_width, far_half_height, -far_distance),
    ]

    # Transform to world space
    origin = Vector(camera_position)
    world_corners = []

    for corner in local_corners:
        v = Vector(corner)
        v.rotate(euler)
        world_corners.append(tuple(origin + v))

    return world_corners


def create_frustum_visualization(
    camera_name: str,
    name: str = "Frustum_Viz",
    near_distance: float = 0.1,
    far_distance: float = 100.0,
) -> Optional[str]:
    """
    Create a visual representation of camera frustum.

    Creates a mesh object showing the frustum volume.

    Args:
        camera_name: Camera object name
        name: Name for the visualization object
        near_distance: Near clip distance
        far_distance: Far clip distance

    Returns:
        Name of created object, or None if failed
    """
    if not HAS_BLENDER:
        return None

    camera = bpy.data.objects.get(camera_name)
    if camera is None or camera.type != 'CAMERA':
        return None

    # Get camera properties
    fov = math.degrees(camera.data.angle)
    aspect = camera.data.sensor_width / camera.data.sensor_height if camera.data.sensor_height > 0 else 16 / 9

    position = tuple(camera.matrix_world.translation)
    rotation = tuple(camera.matrix_world.to_euler('XYZ'))

    # Get frustum corners
    corners = get_projection_bounds(
        position,
        rotation,
        fov,
        near_distance,
        far_distance,
        aspect,
    )

    if len(corners) != 8:
        return None

    # Create mesh
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)

    # Link to scene
    bpy.context.collection.objects.link(obj)

    # Define vertices and faces
    vertices = corners
    faces = [
        (0, 1, 2, 3),  # Near face
        (4, 5, 6, 7),  # Far face
        (0, 4, 5, 1),  # Bottom face
        (2, 6, 7, 3),  # Top face
        (0, 3, 7, 4),  # Left face
        (1, 5, 6, 2),  # Right face
    ]

    mesh.from_pydata(vertices, [], faces)
    mesh.update()

    # Set to wireframe display
    obj.display_type = 'WIRE'

    return obj.name


def estimate_projection_quality(
    hits: List,
    surface_area: float,
) -> dict:
    """
    Estimate projection quality based on ray coverage.

    Args:
        hits: List of RayHit objects
        surface_area: Surface area in square meters

    Returns:
        Dictionary with quality metrics
    """
    if not hits:
        return {
            "coverage": 0.0,
            "density": 0.0,
            "quality": "none",
        }

    hit_count = sum(1 for h in hits if h.hit)

    # Estimate coverage (simplified)
    # In reality, would calculate based on hit distribution
    coverage = min(hit_count / max(len(hits), 1) * 100, 100.0)

    # Density (hits per square meter)
    density = hit_count / max(surface_area, 0.01)

    # Quality rating
    if coverage > 80 and density > 100:
        quality = "excellent"
    elif coverage > 60 and density > 50:
        quality = "good"
    elif coverage > 40 and density > 20:
        quality = "acceptable"
    elif coverage > 20:
        quality = "poor"
    else:
        quality = "insufficient"

    return {
        "coverage": coverage,
        "density": density,
        "hit_count": hit_count,
        "total_rays": len(hits),
        "quality": quality,
    }

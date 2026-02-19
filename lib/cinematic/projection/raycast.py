"""
Frustum Raycasting for Anamorphic Projection

Implements camera frustum raycasting to cast rays from a camera
through image pixel positions onto scene geometry.

Part of Phase 9.0 - Projection Foundation (REQ-ANAM-01)
Beads: blender_gsd-34
"""

from __future__ import annotations
import time
import math
from typing import List, Optional, Tuple, Dict, Any

from .types import (
    RayHit,
    FrustumConfig,
    ProjectionResult,
    SurfaceType,
    SurfaceInfo,
)

# Blender API guard for testing outside Blender
try:
    import bpy
    import mathutils
    from mathutils import Vector, Matrix
    HAS_BLENDER = True
except ImportError:
    HAS_BLENDER = False
    Vector = None
    Matrix = None


def generate_frustum_rays(
    camera_position: Tuple[float, float, float],
    camera_rotation: Tuple[float, float, float],  # Euler degrees
    config: FrustumConfig,
) -> List[Tuple[Vector, Vector]]:
    """
    Generate ray origins and directions for camera frustum.

    Creates a grid of rays from the camera position through
    the image plane, based on FOV and resolution.

    Args:
        camera_position: World position of camera
        camera_rotation: Euler rotation in degrees (XYZ)
        config: Frustum configuration

    Returns:
        List of (origin, direction) tuples for each ray
    """
    if not HAS_BLENDER:
        raise RuntimeError("Blender required for ray generation")

    rays = []

    # Convert rotation to radians and create rotation matrix
    rot_rad = [math.radians(r) for r in camera_rotation]
    euler = mathutils.Euler(rot_rad, 'XYZ')
    rot_matrix = euler.to_matrix().to_4x4()

    # Calculate half-FOV for ray direction calculation
    fov_rad = math.radians(config.fov)
    half_fov = fov_rad / 2.0

    # Calculate aspect ratio
    aspect = config.resolution_x / config.resolution_y

    # Apply subsampling
    step = config.subsample
    start_x = int(config.region_min_x * config.resolution_x)
    start_y = int(config.region_min_y * config.resolution_y)
    end_x = int(config.region_max_x * config.resolution_x)
    end_y = int(config.region_max_y * config.resolution_y)

    # Camera forward direction (negative Z in Blender camera space)
    forward = Vector((0.0, 0.0, -1.0))
    forward.rotate(euler)

    # Camera right and up vectors
    right = Vector((1.0, 0.0, 0.0))
    right.rotate(euler)
    up = Vector((0.0, 1.0, 0.0))
    up.rotate(euler)

    origin = Vector(camera_position)

    # Generate rays for each pixel
    for y in range(start_y, end_y, step):
        for x in range(start_x, end_x, step):
            # Normalize pixel coordinates to -1 to 1
            ndc_x = (2.0 * x / config.resolution_x - 1.0) * aspect
            ndc_y = 2.0 * y / config.resolution_y - 1.0

            # Calculate ray direction based on FOV
            # tan(half_fov) gives the offset at z=-1
            tan_half = math.tan(half_fov)
            offset_x = ndc_x * tan_half
            offset_y = ndc_y * tan_half

            # Direction in camera space
            dir_cam = Vector((offset_x, offset_y, -1.0))
            dir_cam.normalize()

            # Transform to world space
            direction = Vector(dir_cam)
            direction.rotate(euler)

            rays.append((origin.copy(), direction))

    return rays


def cast_ray(
    origin: Vector,
    direction: Vector,
    max_distance: float = 1000.0,
    ignore_objects: Optional[List[str]] = None,
) -> RayHit:
    """
    Cast a single ray and return hit information.

    Uses Blender's BVH tree for fast ray-scene intersection.

    Args:
        origin: Ray start position
        direction: Ray direction (normalized)
        max_distance: Maximum ray travel distance
        ignore_objects: Object names to ignore

    Returns:
        RayHit with intersection information
    """
    if not HAS_BLENDER:
        raise RuntimeError("Blender required for raycasting")

    ignore_set = set(ignore_objects or [])

    best_hit = RayHit(hit=False)

    # Check all mesh objects in the scene
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH':
            continue
        if obj.name in ignore_set:
            continue

        # Get world matrix and inverted for coordinate conversion
        world_matrix = obj.matrix_world
        world_matrix_inv = world_matrix.inverted()

        # Transform ray to object space
        origin_obj = world_matrix_inv @ origin
        direction_obj = world_matrix_inv @ (origin + direction) - origin_obj
        direction_obj.normalize()

        # Raycast on mesh
        hit, location, normal, face_index = obj.ray_cast(origin_obj, direction_obj)

        if hit:
            # Transform back to world space
            world_location = world_matrix @ location
            world_normal = world_matrix.transposed() @ normal
            world_normal.normalize()

            # Calculate distance
            distance = (world_location - origin).length

            # Check if this is the closest hit so far
            if distance < max_distance and (not best_hit.hit or distance < best_hit.distance):
                best_hit = RayHit(
                    position=tuple(world_location),
                    normal=tuple(world_normal),
                    distance=distance,
                    object_name=obj.name,
                    face_index=face_index,
                    hit=True,
                )
                max_distance = distance  # Update for early termination

    return best_hit


def project_from_camera(
    camera_name: str,
    config: FrustumConfig,
    source_image_path: Optional[str] = None,
) -> ProjectionResult:
    """
    Project from a camera viewpoint onto scene geometry.

    Main entry point for frustum raycasting. Casts rays from
    the camera through the image plane and records all hits.

    Args:
        camera_name: Name of the camera object in Blender
        config: Frustum configuration
        source_image_path: Optional image to sample colors from

    Returns:
        ProjectionResult with all ray hit information
    """
    if not HAS_BLENDER:
        raise RuntimeError("Blender required for projection")

    start_time = time.time()

    # Get camera object
    camera = bpy.data.objects.get(camera_name)
    if camera is None or camera.type != 'CAMERA':
        raise ValueError(f"Camera '{camera_name}' not found or not a camera")

    # Get camera position and rotation
    camera_position = tuple(camera.matrix_world.translation)
    camera_rotation = tuple(camera.matrix_world.to_euler('XYZ'))

    # Generate rays
    rays = generate_frustum_rays(camera_position, camera_rotation, config)

    # Load source image if provided
    source_pixels = None
    if source_image_path:
        try:
            source_image = bpy.data.images.load(source_image_path, check_existing=True)
            source_pixels = list(source_image.pixels)
            source_width = source_image.size[0]
            source_height = source_image.size[1]
        except Exception:
            source_image_path = ""  # Clear if failed to load

    # Cast all rays
    hits: List[RayHit] = []
    hits_by_object: Dict[str, List[RayHit]] = {}

    ignore_patterns = config.ignore_patterns

    for idx, (origin, direction) in enumerate(rays):
        # Calculate pixel coordinates
        # Reverse engineer from index
        total_x = int((config.region_max_x - config.region_min_x) * config.resolution_x / config.subsample)
        pixel_x = config.region_min_x * config.resolution_x + (idx % total_x) * config.subsample
        pixel_y = config.region_min_y * config.resolution_y + (idx // total_x) * config.subsample

        # Cast ray
        hit = cast_ray(
            origin,
            direction,
            max_distance=config.far_clip,
            ignore_objects=ignore_patterns,
        )

        # Add pixel coordinates
        hit.pixel_x = int(pixel_x)
        hit.pixel_y = int(pixel_y)

        # Sample color from source image if available
        if source_pixels and hit.hit:
            # Convert pixel coordinates to image coordinates
            img_x = int((pixel_x / config.resolution_x) * source_width)
            img_y = int((pixel_y / config.resolution_y) * source_height)

            # Clamp to image bounds
            img_x = min(max(img_x, 0), source_width - 1)
            img_y = min(max(img_y, 0), source_height - 1)

            # Get pixel index (RGBA = 4 floats per pixel)
            pixel_idx = (img_y * source_width + img_x) * 4

            if pixel_idx + 3 < len(source_pixels):
                hit.color = (
                    source_pixels[pixel_idx],
                    source_pixels[pixel_idx + 1],
                    source_pixels[pixel_idx + 2],
                    source_pixels[pixel_idx + 3],
                )

        hits.append(hit)

        # Group by object
        if hit.hit:
            if hit.object_name not in hits_by_object:
                hits_by_object[hit.object_name] = []
            hits_by_object[hit.object_name].append(hit)

    # Build result
    result = ProjectionResult(
        hits=hits,
        hits_by_object=hits_by_object,
        total_rays=len(rays),
        hit_count=sum(1 for h in hits if h.hit),
        miss_count=sum(1 for h in hits if not h.hit),
        process_time=time.time() - start_time,
        camera_name=camera_name,
        source_image=source_image_path,
        config=config,
    )

    return result


def detect_surfaces_in_frustum(
    camera_name: str,
    config: FrustumConfig,
) -> List[SurfaceInfo]:
    """
    Detect and classify surfaces within camera frustum.

    Analyzes scene geometry to find surfaces that could be
    used for projection, classified by type (floor, wall, etc.).

    Args:
        camera_name: Name of the camera object
        config: Frustum configuration

    Returns:
        List of SurfaceInfo for detected surfaces
    """
    if not HAS_BLENDER:
        raise RuntimeError("Blender required for surface detection")

    camera = bpy.data.objects.get(camera_name)
    if camera is None or camera.type != 'CAMERA':
        raise ValueError(f"Camera '{camera_name}' not found")

    surfaces = []

    # Get camera position
    camera_pos = camera.matrix_world.translation

    # Get camera forward direction
    forward = Vector((0.0, 0.0, -1.0))
    forward.rotate(camera.matrix_world.to_euler('XYZ'))

    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH':
            continue

        # Get bounding box center in world space
        bbox = [obj.matrix_world @ Vector(corner) for corner in obj.bound_box]
        center = sum(bbox, Vector()) / len(bbox)

        # Check if object is roughly in front of camera
        to_obj = (center - camera_pos).normalized()
        dot = forward.dot(to_obj)

        if dot < 0:  # Behind camera
            continue

        # Calculate dominant normal from face normals
        normals = []
        for poly in obj.data.polygons:
            world_normal = obj.matrix_world @ poly.normal
            normals.append(world_normal.normalized())

        if not normals:
            continue

        # Average normal
        avg_normal = sum(normals, Vector()) / len(normals)
        avg_normal.normalize()

        # Classify surface type based on normal
        surface_type = SurfaceType.CUSTOM
        if avg_normal.z > 0.7:  # Facing up
            surface_type = SurfaceType.FLOOR
        elif avg_normal.z < -0.7:  # Facing down
            surface_type = SurfaceType.CEILING
        elif abs(avg_normal.z) < 0.3:  # Mostly horizontal
            surface_type = SurfaceType.WALL

        # Check filter
        if config.surface_filter != SurfaceType.ALL:
            if surface_type != config.surface_filter:
                continue

        # Calculate surface area (approximate)
        area = sum(poly.area for poly in obj.data.polygons)
        # Scale by object scale
        scale = obj.scale
        area *= (scale.x * scale.y * scale.z) ** (1/3)

        # Check for UV layers
        has_uv = len(obj.data.uv_layers) > 0
        uv_layer = obj.data.uv_layers.active.name if has_uv else ""

        # Check if in frustum (simplified - use raycast)
        in_frustum = True  # Simplified, actual check would be more complex

        surface_info = SurfaceInfo(
            object_name=obj.name,
            surface_type=surface_type,
            center=tuple(center),
            normal=tuple(avg_normal),
            area=area,
            face_count=len(obj.data.polygons),
            in_frustum=in_frustum,
            has_uv=has_uv,
            uv_layer=uv_layer,
        )

        surfaces.append(surface_info)

    return surfaces


def get_pixel_ray(
    camera_name: str,
    pixel_x: int,
    pixel_y: int,
    resolution: Tuple[int, int],
) -> Tuple[Vector, Vector]:
    """
    Get a single ray for a specific pixel.

    Useful for interactive picking or single-ray queries.

    Args:
        camera_name: Camera object name
        pixel_x: X pixel coordinate
        pixel_y: Y pixel coordinate
        resolution: (width, height) of image

    Returns:
        (origin, direction) tuple for the ray
    """
    if not HAS_BLENDER:
        raise RuntimeError("Blender required")

    camera = bpy.data.objects.get(camera_name)
    if camera is None or camera.type != 'CAMERA':
        raise ValueError(f"Camera '{camera_name}' not found")

    # Get camera transform
    camera_pos = camera.matrix_world.translation
    euler = camera.matrix_world.to_euler('XYZ')

    # Get camera FOV
    fov = math.degrees(camera.data.angle)

    # Calculate ray direction
    aspect = resolution[0] / resolution[1]

    ndc_x = (2.0 * pixel_x / resolution[0] - 1.0) * aspect
    ndc_y = 2.0 * pixel_y / resolution[1] - 1.0

    tan_half = math.tan(math.radians(fov / 2))
    offset_x = ndc_x * tan_half
    offset_y = ndc_y * tan_half

    dir_cam = Vector((offset_x, offset_y, -1.0))
    dir_cam.normalize()

    direction = Vector(dir_cam)
    direction.rotate(euler)

    origin = Vector(camera_pos)

    return origin, direction

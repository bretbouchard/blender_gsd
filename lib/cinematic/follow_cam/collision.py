"""
Follow Camera Collision Detection

Implements raycast-based collision detection for follow camera:
- Raycast detection from camera to subject
- Spherecast for wider detection radius
- Frustum check for objects in view
- Collision layer support
- Ignore list (transparent, triggers, subject)

Uses existing raycasting from lib.cinematic.projection.raycast

Part of Phase 8.x - Follow Camera System
Beads: blender_gsd-57, 58
"""

from __future__ import annotations
import math
from typing import Tuple, Optional, List, Dict, Any, Set

from .types import (
    ObstacleInfo,
    ObstacleResponse,
    FollowCameraConfig,
)

# Blender API guard for testing outside Blender
try:
    import bpy
    import mathutils
    from mathutils import Vector, Matrix
    HAS_BLENDER = True
except ImportError:
    HAS_BLENDER = False
    # Import fallback Vector from follow_modes
    from .follow_modes import Vector


# =============================================================================
# COLLISION DETECTION
# =============================================================================

def detect_obstacles(
    camera_position: Tuple[float, float, float],
    target_position: Tuple[float, float, float],
    config: FollowCameraConfig,
    additional_ignore: Optional[List[str]] = None,
) -> List[ObstacleInfo]:
    """
    Detect obstacles between camera and target.

    Performs multiple raycast checks to find obstacles:
    1. Direct line from camera to target
    2. Spherecast for wider detection
    3. Multiple sample rays for coverage

    Args:
        camera_position: Current camera world position
        target_position: Target subject world position
        config: Camera configuration with collision settings
        additional_ignore: Additional objects to ignore

    Returns:
        List of detected ObstacleInfo objects
    """
    if not config.collision_enabled or not HAS_BLENDER:
        return []

    obstacles: List[ObstacleInfo] = []
    cam_pos = Vector(camera_position)
    target_pos = Vector(target_position)

    # Build ignore set
    ignore_set: Set[str] = set(config.ignore_objects)
    if additional_ignore:
        ignore_set.update(additional_ignore)

    # Calculate direction and distance
    direction = target_pos - cam_pos
    distance = direction.length()
    direction_normalized = direction.normalized()

    # 1. Direct raycast
    direct_hit = _raycast(
        origin=cam_pos,
        direction=direction_normalized,
        max_distance=distance,
        ignore_objects=ignore_set,
        collision_layers=config.collision_layers,
    )
    if direct_hit:
        obstacles.append(direct_hit)

    # 2. Spherecast (multiple rays around the main ray)
    sphere_hits = _spherecast(
        origin=cam_pos,
        direction=direction_normalized,
        max_distance=distance,
        radius=config.collision_radius,
        ignore_objects=ignore_set,
        collision_layers=config.collision_layers,
    )
    for hit in sphere_hits:
        if hit and not _obstacle_already_detected(obstacles, hit):
            obstacles.append(hit)

    # 3. Check behind camera (for backing away)
    back_hit = _raycast(
        origin=cam_pos,
        direction=-direction_normalized,  # Behind camera
        max_distance=config.min_obstacle_distance,
        ignore_objects=ignore_set,
        collision_layers=config.collision_layers,
    )
    if back_hit:
        # Mark as back obstacle
        back_hit.response = ObstacleResponse.BACK_AWAY
        if not _obstacle_already_detected(obstacles, back_hit):
            obstacles.append(back_hit)

    # Sort by distance
    obstacles.sort(key=lambda o: o.distance)

    return obstacles


def _raycast(
    origin: Vector,
    direction: Vector,
    max_distance: float,
    ignore_objects: Set[str],
    collision_layers: List[str],
) -> Optional[ObstacleInfo]:
    """
    Perform a single raycast.

    Args:
        origin: Ray start position
        direction: Ray direction (normalized)
        max_distance: Maximum ray travel distance
        ignore_objects: Object names to ignore
        collision_layers: Physics layers to check

    Returns:
        ObstacleInfo if hit, None otherwise
    """
    if not HAS_BLENDER:
        return None

    best_hit: Optional[ObstacleInfo] = None
    best_distance = max_distance

    # Check all mesh objects
    for obj in bpy.context.scene.objects:
        if obj.type != 'MESH':
            continue
        if obj.name in ignore_objects:
            continue

        # Get world matrix
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
            hit_distance = (world_location - origin).length()

            # Check if this is the closest hit
            if hit_distance < best_distance and hit_distance > 0.001:
                # Determine if transparent or trigger
                is_transparent = _is_transparent_object(obj)
                is_trigger = _is_trigger_object(obj)

                # Determine response type
                if is_transparent:
                    response = ObstacleResponse.ZOOM_THROUGH
                else:
                    response = ObstacleResponse.PUSH_FORWARD

                best_hit = ObstacleInfo(
                    object_name=obj.name,
                    position=tuple(world_location),
                    normal=tuple(world_normal),
                    distance=hit_distance,
                    is_transparent=is_transparent,
                    is_trigger=is_trigger,
                    response=response,
                )
                best_distance = hit_distance

    return best_hit


def _spherecast(
    origin: Vector,
    direction: Vector,
    max_distance: float,
    radius: float,
    ignore_objects: Set[str],
    collision_layers: List[str],
) -> List[ObstacleInfo]:
    """
    Perform a spherecast (multiple rays around the main ray).

    Casts rays in a circular pattern around the main direction
    to detect wider obstacles.

    Args:
        origin: Ray start position
        direction: Main ray direction
        max_distance: Maximum ray travel distance
        radius: Sphere radius (offset from main ray)
        ignore_objects: Object names to ignore
        collision_layers: Physics layers to check

    Returns:
        List of ObstacleInfo for all hits
    """
    hits: List[ObstacleInfo] = []

    if not HAS_BLENDER:
        return hits

    # Calculate perpendicular vectors for offset
    up = Vector((0.0, 0.0, 1.0))
    if abs(direction.dot(up)) > 0.9:
        up = Vector((1.0, 0.0, 0.0))

    right = direction.cross(up).normalized()
    up = right.cross(direction).normalized()

    # Cast rays in circular pattern
    num_rays = 8
    for i in range(num_rays):
        angle = (2 * math.pi * i) / num_rays
        offset = right * (radius * math.cos(angle)) + up * (radius * math.sin(angle))

        # Offset origin
        offset_origin = origin + offset

        hit = _raycast(
            origin=offset_origin,
            direction=direction,
            max_distance=max_distance,
            ignore_objects=ignore_objects,
            collision_layers=collision_layers,
        )

        if hit:
            hits.append(hit)

    return hits


def _obstacle_already_detected(
    obstacles: List[ObstacleInfo],
    new_obstacle: ObstacleInfo,
) -> bool:
    """Check if an obstacle is already in the list."""
    for obs in obstacles:
        if obs.object_name == new_obstacle.object_name:
            # Same object, check if same general area
            dist = math.sqrt(
                (obs.position[0] - new_obstacle.position[0]) ** 2 +
                (obs.position[1] - new_obstacle.position[1]) ** 2 +
                (obs.position[2] - new_obstacle.position[2]) ** 2
            )
            if dist < 0.5:  # Within 0.5 meters
                return True
    return False


def _is_transparent_object(obj) -> bool:
    """Check if object has transparent material."""
    if not HAS_BLENDER:
        return False

    try:
        for slot in obj.material_slots:
            if slot.material:
                # Check for transparency settings
                if hasattr(slot.material, 'blend_method'):
                    if slot.material.blend_method != 'OPAQUE':
                        return True
                # Check alpha
                if hasattr(slot.material, 'use_backface_culling'):
                    if slot.material.use_backface_culling:
                        return True
    except Exception:
        pass

    # Check custom property
    if obj.get('transparent', False):
        return True

    # Check name patterns
    transparent_patterns = ['glass', 'window', 'transparent', 'water']
    name_lower = obj.name.lower()
    if any(p in name_lower for p in transparent_patterns):
        return True

    return False


def _is_trigger_object(obj) -> bool:
    """Check if object is a trigger volume."""
    if not HAS_BLENDER:
        return False

    # Check custom property
    if obj.get('is_trigger', False):
        return True

    # Check name patterns
    trigger_patterns = ['trigger', 'volume', 'zone', 'sensor']
    name_lower = obj.name.lower()
    if any(p in name_lower for p in trigger_patterns):
        return True

    return False


# =============================================================================
# OBSTACLE RESPONSE (blender_gsd-58)
# =============================================================================

def calculate_avoidance_position(
    camera_position: Tuple[float, float, float],
    target_position: Tuple[float, float, float],
    obstacles: List[ObstacleInfo],
    config: FollowCameraConfig,
) -> Tuple[Tuple[float, float, float], str]:
    """
    Calculate camera position avoiding obstacles.

    Applies appropriate response strategy based on obstacle types:
    - push_forward: Move camera closer to subject
    - orbit_away: Rotate camera around obstacle
    - raise_up: Move camera higher
    - zoom_through: Pass through transparent objects
    - back_away: Move camera back from wall behind

    Args:
        camera_position: Current camera position
        target_position: Target subject position
        obstacles: List of detected obstacles
        config: Camera configuration

    Returns:
        Tuple of (new_position, response_description)
    """
    if not obstacles:
        return camera_position, "no_obstacles"

    cam_pos = Vector(camera_position)
    target_pos = Vector(target_position)

    # Find the most important obstacle (closest non-transparent)
    primary_obstacle = _get_primary_obstacle(obstacles)

    if not primary_obstacle:
        # All obstacles are transparent or triggers
        return camera_position, "transparent_only"

    # Apply response based on obstacle type
    if primary_obstacle.response == ObstacleResponse.ZOOM_THROUGH:
        # Pass through transparent
        return camera_position, "zoom_through"

    elif primary_obstacle.response == ObstacleResponse.PUSH_FORWARD:
        return _response_push_forward(
            cam_pos, target_pos, primary_obstacle, config
        )

    elif primary_obstacle.response == ObstacleResponse.ORBIT_AWAY:
        return _response_orbit_away(
            cam_pos, target_pos, primary_obstacle, config
        )

    elif primary_obstacle.response == ObstacleResponse.RAISE_UP:
        return _response_raise_up(
            cam_pos, target_pos, primary_obstacle, config
        )

    elif primary_obstacle.response == ObstacleResponse.BACK_AWAY:
        return _response_back_away(
            cam_pos, target_pos, primary_obstacle, config
        )

    else:
        # Default to push forward
        return _response_push_forward(
            cam_pos, target_pos, primary_obstacle, config
        )


def _get_primary_obstacle(obstacles: List[ObstacleInfo]) -> Optional[ObstacleInfo]:
    """Get the most important obstacle to respond to."""
    for obs in obstacles:
        if not obs.is_transparent and not obs.is_trigger:
            return obs
    return None


def _response_push_forward(
    cam_pos: Vector,
    target_pos: Vector,
    obstacle: ObstacleInfo,
    config: FollowCameraConfig,
) -> Tuple[Tuple[float, float, float], str]:
    """
    Push camera closer to target to avoid obstacle.

    Moves camera along the line to target, stopping before the obstacle.
    """
    direction = target_pos - cam_pos
    distance = direction.length()
    direction_normalized = direction.normalized()

    # Calculate how far to push forward
    # Stop at min_obstacle_distance from obstacle
    push_distance = obstacle.distance - config.min_obstacle_distance

    # Clamp to min_distance from target
    new_distance = distance - push_distance
    if new_distance < config.min_distance:
        new_distance = config.min_distance

    # Calculate new position
    new_pos = target_pos - direction_normalized * new_distance

    return tuple(new_pos.to_tuple() if hasattr(new_pos, 'to_tuple') else new_pos._values), "push_forward"


def _response_orbit_away(
    cam_pos: Vector,
    target_pos: Vector,
    obstacle: ObstacleInfo,
    config: FollowCameraConfig,
) -> Tuple[Tuple[float, float, float], str]:
    """
    Orbit camera around target to avoid obstacle.

    Rotates the camera position around the target.
    """
    # Calculate current angle
    offset = cam_pos - target_pos
    current_angle = math.atan2(offset.x, offset.y)

    # Determine rotation direction based on obstacle normal
    normal = Vector(obstacle.normal)
    rotate_direction = 1 if normal.x > 0 else -1

    # Rotate by fixed amount
    rotation_amount = math.radians(30) * rotate_direction
    new_angle = current_angle + rotation_amount

    # Calculate new position
    distance = offset.length()
    new_offset = Vector((
        math.sin(new_angle) * distance,
        math.cos(new_angle) * distance,
        offset.z,
    ))

    new_pos = target_pos + new_offset

    return tuple(new_pos.to_tuple() if hasattr(new_pos, 'to_tuple') else new_pos._values), "orbit_away"


def _response_raise_up(
    cam_pos: Vector,
    target_pos: Vector,
    obstacle: ObstacleInfo,
    config: FollowCameraConfig,
) -> Tuple[Tuple[float, float, float], str]:
    """
    Raise camera to clear obstacle.

    Moves camera higher while maintaining distance.
    """
    # Calculate current distance
    offset = cam_pos - target_pos
    distance = offset.length()

    # Calculate raise amount
    raise_amount = config.min_obstacle_distance + obstacle.distance * 0.2

    # Create new position with raised height
    new_pos = cam_pos + Vector((0.0, 0.0, raise_amount))

    # Clamp to max height
    height_above_target = (new_pos - target_pos).z
    if height_above_target > config.max_height:
        new_pos.z = target_pos.z + config.max_height

    return tuple(new_pos.to_tuple() if hasattr(new_pos, 'to_tuple') else new_pos._values), "raise_up"


def _response_back_away(
    cam_pos: Vector,
    target_pos: Vector,
    obstacle: ObstacleInfo,
    config: FollowCameraConfig,
) -> Tuple[Tuple[float, float, float], str]:
    """
    Move camera forward (away from wall behind).

    Used when there's an obstacle directly behind the camera.
    """
    direction = (target_pos - cam_pos).normalized()

    # Move camera forward
    move_distance = config.min_obstacle_distance - obstacle.distance
    if move_distance < 0:
        move_distance = config.min_obstacle_distance

    new_pos = cam_pos + direction * move_distance

    return tuple(new_pos.to_tuple() if hasattr(new_pos, 'to_tuple') else new_pos._values), "back_away"


# =============================================================================
# FRUSTUM CHECK
# =============================================================================

def check_frustum_obstruction(
    camera_position: Tuple[float, float, float],
    camera_rotation: Tuple[float, float, float],
    target_position: Tuple[float, float, float],
    fov: float,
    near_clip: float = 0.1,
    far_clip: float = 100.0,
) -> List[ObstacleInfo]:
    """
    Check for objects obstructing the camera's view frustum.

    Casts rays through the frustum to detect objects that
    might partially or fully obscure the subject.

    Args:
        camera_position: Camera world position
        camera_rotation: Camera Euler rotation (degrees)
        target_position: Target subject position
        fov: Field of view in degrees
        near_clip: Near clipping distance
        far_clip: Far clipping distance

    Returns:
        List of obstacles in frustum
    """
    if not HAS_BLENDER:
        return []

    obstacles: List[ObstacleInfo] = []
    cam_pos = Vector(camera_position)

    # Calculate camera forward direction
    rot_rad = [math.radians(r) for r in camera_rotation]

    # Simplified forward calculation
    yaw = rot_rad[2]  # Z rotation
    pitch = rot_rad[0]  # X rotation

    forward = Vector((
        math.sin(yaw) * math.cos(pitch),
        math.cos(yaw) * math.cos(pitch),
        -math.sin(pitch),
    )).normalized()

    # Cast rays at different points in frustum
    up = Vector((0.0, 0.0, 1.0))
    right = forward.cross(up).normalized()
    up = right.cross(forward).normalized()

    # Sample points in frustum
    num_samples = 9  # 3x3 grid
    half_fov_rad = math.radians(fov / 2)

    for i in range(3):
        for j in range(3):
            # Calculate ray direction
            x_offset = (i - 1) * math.tan(half_fov_rad)
            y_offset = (j - 1) * math.tan(half_fov_rad)

            ray_dir = forward + right * x_offset + up * y_offset
            ray_dir.normalize()

            hit = _raycast(
                origin=cam_pos,
                direction=ray_dir,
                max_distance=far_clip,
                ignore_objects=set(),
                collision_layers=["Default"],
            )

            if hit and not _obstacle_already_detected(obstacles, hit):
                obstacles.append(hit)

    return obstacles


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_clearance_distance(
    position: Tuple[float, float, float],
    direction: Tuple[float, float, float],
    config: FollowCameraConfig,
) -> float:
    """
    Get clearance distance in a direction.

    Useful for checking how much space the camera has to move.

    Args:
        position: Starting position
        direction: Direction to check
        config: Camera configuration

    Returns:
        Distance to nearest obstacle, or max distance if clear
    """
    if not HAS_BLENDER:
        return 1000.0

    pos = Vector(position)
    dir_vec = Vector(direction).normalized()

    hit = _raycast(
        origin=pos,
        direction=dir_vec,
        max_distance=1000.0,
        ignore_objects=set(config.ignore_objects),
        collision_layers=config.collision_layers,
    )

    if hit:
        return hit.distance
    else:
        return 1000.0
